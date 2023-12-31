import sys
import random
import string
import base64
import subprocess
import tempfile
import os
import argparse

WRAP_WITH_PRAGMA = False
USE_BASE64 = True
def peek_atom_info(atom):
    
    header_size = 8
    tmp_size = int.from_bytes(infile.read(4), byteorder = "big")
    tmp_type = infile.read(4).decode("ascii")
    if tmp_size == 1:
        header_size = 16
        tmp_size = int.from_bytes(infile.read(8), byteorder = "big")
        infile.seek(-8,1)
    infile.seek(-8,1)
    return tmp_size, tmp_type, header_size

def fix_stco(atom, offset, item_len):
    assert len(atom) >= 8, f'STCO header requires 8 bytes, atom ({len(atom)}) not long enough.'
    
    r  = atom[0:8]
    entries = int.from_bytes(atom[4:8], byteorder = "big")
    assert len(atom) >= 8 + item_len * entries, f'STCO contains {entries} entries, each {item_len} bytes long. Atom ({len(atom)}) not long enough.'
    
    for i in range(entries):
        entry  = int.from_bytes(atom[8 + i * item_len: 8 + i * item_len + item_len], byteorder = 'big')
        entry += offset
        r     += int.to_bytes(entry, length = item_len, byteorder = 'big')
    
    return r

def traverse_atoms(box, offset):
    PARENT_ATOMS = {b'moov', b'trak', b'mdia', b'minf', b'stbl'}
    box_base = 0
    r = b''
    while box_base < len(box):
        assert box_base + 8 <= len(box), f'Parent box size {len(box)}, {box_base} bytes processed. The remaining cannot hold a box.'
        box_len = int.from_bytes(box[box_base + 0: box_base + 4], byteorder = "big")
        box_tag = box[box_base + 4:box_base + 8]
        hdr_len = 8
        #print(f'box {box_tag} at {box_base} len {box_len}')
        if box_len == 1:
            assert box_base + 16 <= len(box), f'Current box requires additional length field, parent box cannot hold.'
            box_len = int.from_bytes(box[box_base + 8: box_base + 16], byteorder = "big")
            hdr_len = 16
        assert box_base + box_len <= len(box), f'Current box at offset {box_base}, with size {box_len}, exceeding parent box size {len(box)}.'
        child_box = box[box_base : box_base + box_len]
        if box_tag in PARENT_ATOMS:
            r += child_box[:hdr_len] + traverse_atoms(child_box[hdr_len:], offset)
        elif box_tag == b'stco':
            r += child_box[:hdr_len] + fix_stco(child_box[hdr_len:], offset = offset, item_len = 4)
        elif box_tag == b'co64':
            r += child_box[:hdr_len] + fix_stco(child_box[hdr_len:], offset = offset, item_len = 8)
        else:
            r += child_box
        box_base += box_len
    return r

def build_header_atom(mp4):
    if not WRAP_WITH_PRAGMA:
        helper_func_name = b'foo'+ ''.join(random.choices(string.ascii_letters + string.digits, k=6)).encode()
        print(f'helper function {helper_func_name.decode()}')
    
    d_sequence = b'--------'
    while d_sequence in mp4:
        d_sequence = ''.join(random.choices(string.ascii_letters, k=8)).encode()
    print(f'd sequence "{d_sequence.decode()}"')
    
    d_sequence_2 = None
    if WRAP_WITH_PRAGMA:
        d_sequence_2 = b'========'
        while d_sequence_2 in mp4 or d_sequence_2 == d_sequence:
            d_sequence_2 = ''.join(random.choices(string.ascii_letters, k=8)).encode()
        print(f'd sequence 2"{d_sequence_2.decode()}"')
    
    inc_guard = 'MP4_AS_HEADER_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    small_header  = b'\x00\x00\x00\x20' #length 
    small_header += b'//hello world\n'
    #small_header += b'void ' + helper_func_name + b'(){\n'
    small_header += b'//'
    small_header += b' ' * (0x20 - len(small_header))
    
    long_header  = b'\x00\x00\x09\x00'
    long_header += b'skip\n'
    long_header += b'#pragma once\n'
    long_header += b'#ifndef ' + inc_guard.encode() + b'\n'
    long_header += b'#define '+ inc_guard.encode() + b'\n'
    long_header += b'#pragma GCC system_header\n'
    long_header += b'#pragma clang diagnostic push\n'
    long_header += b'#pragma clang diagnostic ignored "-Winvalid-source-encoding"\n'
    if WRAP_WITH_PRAGMA:
        long_header += b'_Pragma(R"' + d_sequence_2 + b'(comment(user, R"' + d_sequence + b'('
    else:
        long_header += b'inline void ' + helper_func_name + b'(){(void)R"' + d_sequence + b'('
    long_header += b' ' * (0x900 - len(long_header))
    
    header = small_header + long_header
    assert len(header)==0x920
    return header, (d_sequence, d_sequence_2)

def build_tailing_atom(ts, user):
    d_sequence, d_sequence_2 = user
    tailer  = b'\x00\x00\x00\x00'     #placeholder for atom size
    tailer += b'wtvr'                #whatever tag without a meaning in mp4
    if WRAP_WITH_PRAGMA:
        tailer += b')' + d_sequence + b'"))' + d_sequence_2 + b'")\n'
    else:
        tailer += b')' + d_sequence + b'";}\n'
    
    namespace_tag   = 'mp4header_namespace_'+ ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    if USE_BASE64:
        b64_alltext = base64.standard_b64encode(ts).decode() # some compilers have limit on string length.
        b64_processed = 0
        b64_txt = ''
        while b64_processed < len(b64_alltext):
            b64_txt += '"' + b64_alltext[b64_processed:b64_processed + 65536] + '",\n'
            b64_processed += 65536
        video_data = f'''
            {namespace_tag}_WEAK const char * {namespace_tag}_video_data[] = {{
                {b64_txt}
            }};
            '''
        BASE64_ENCODE_TABLE = string.ascii_uppercase + string.ascii_lowercase + string.digits + '+/'
        base64_lookup_table = f"const unsigned char {namespace_tag}_b64_table[256][6]={{"
        for i in range(256):
            if i != 0:
                base64_lookup_table += ','
            if chr(i) in BASE64_ENCODE_TABLE:
                v = BASE64_ENCODE_TABLE.find(chr(i))
                base64_lookup_table += f"{{{v * 4},{v // 16},{(v % 16) * 16},{v // 4},{(v % 4) * 64},{v}}}"
            else:
                base64_lookup_table += '{' + ','.join(['0']*6)+'}'
        base64_lookup_table += '};\n'
    else:
        incbin_txt = ',\n'.join(','.join(str(int(b)) for b in ts[j:j + 16384]) for j in range(0,len(ts),16384)) + '\n'
            
        video_data = f'''
            {namespace_tag}_WEAK unsigned char {namespace_tag}_video_data[] = {{
                {incbin_txt}
            }};
            '''
    
    print(f'namespace {namespace_tag}')
    cpp_decoder_code = f'''
        #include <stdlib.h>
        #include <stdio.h>
        #include <string.h>
        #ifdef _WIN32
        #include <Windows.h>
        #define {namespace_tag}_WEAK __declspec(selectany)
        #else
        #ifdef __linux__
        #define {namespace_tag}_WEAK __attribute__((weak))
        #define _GNU_SOURCE
        #include <sys/mman.h>
        #include <sys/wait.h>
        #include <unistd.h>
        #include <sys/types.h>
        #else
        #error "Unsupported system"
        #endif
        #endif
        #ifdef __cplusplus
        namespace {namespace_tag}{{
        #endif
        '''    
    cpp_decoder_code += video_data
    
    windows_prepare_decoder = f'''
        SECURITY_ATTRIBUTES sa;
        sa.nLength = sizeof(SECURITY_ATTRIBUTES);
        sa.lpSecurityDescriptor = NULL;
        sa.bInheritHandle = TRUE;
        
        char TempPath[MAX_PATH];
        #ifdef GetTempPath2
        GetTempPath2A(MAX_PATH,TempPath);
        #else
        GetTempPathA(MAX_PATH,TempPath);
        #endif
        char TempFilePath[MAX_PATH];
        GetTempFileNameA(TempPath,"",0,TempFilePath);
        HANDLE memfd = CreateFileA(TempFilePath, GENERIC_WRITE | GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE, &sa, OPEN_EXISTING ,FILE_ATTRIBUTE_TEMPORARY|FILE_FLAG_DELETE_ON_CLOSE,NULL);
        LARGE_INTEGER file_size;
        file_size.QuadPart = {len(ts) + 2}ull;
        SetFilePointerEx(memfd, file_size, NULL, FILE_BEGIN);
        SetEndOfFile(memfd);
        ULARGE_INTEGER required_size;
        required_size.QuadPart = {len(ts) + 2}ull;
        HANDLE hFileMapping = CreateFileMappingA(memfd, NULL, PAGE_READWRITE, required_size.HighPart, required_size.LowPart, NULL);
        void* data = MapViewOfFile(hFileMapping, FILE_MAP_ALL_ACCESS, 0, 0, 0);
        '''
    windows_cleanup_decoder = f'''
        FlushViewOfFile(data, 0);
        UnmapViewOfFile(data);
        CloseHandle(hFileMapping);
        file_size.QuadPart = 0ull;
        SetFilePointerEx(memfd, file_size, NULL, FILE_BEGIN);
        '''
    linux_prepare_decoder = f'''
        int memfd = memfd_create("ts_video", 0);
        ftruncate(memfd, {len(ts) + 2});
        void* data = mmap(NULL, {len(ts) + 2}, PROT_READ|PROT_WRITE, MAP_SHARED, memfd, 0);
        '''
    linux_cleanup_decoder = f'''
        msync(data,{len(ts) + 2},MS_SYNC);
        munmap(data,{len(ts) + 2});
        ftruncate(memfd, {len(ts)});
        lseek(memfd,0,SEEK_SET);
        '''
    if USE_BASE64:
        cpp_decoder_code += base64_lookup_table
        core_decoder = f'''
            unsigned char* dp = (unsigned char*)data;
            for(size_t i=0;i<sizeof({namespace_tag}_video_data)/sizeof({namespace_tag}_video_data[0]);i++){{
                for(const char* s={namespace_tag}_video_data[i];*s;s+=4){{
                    dp[0] = {namespace_tag}_b64_table[s[0]][0] | {namespace_tag}_b64_table[s[1]][1];
                    dp[1] = {namespace_tag}_b64_table[s[1]][2] | {namespace_tag}_b64_table[s[2]][3];
                    dp[2] = {namespace_tag}_b64_table[s[2]][4] | {namespace_tag}_b64_table[s[3]][5];
                    dp+=3;
                }}
            }}
            '''
    else:
        core_decoder = f'''
            memcpy(data, {namespace_tag}_video_data, sizeof({namespace_tag}_video_data));
            '''
    decode_video = f'''
        #ifdef _WIN32
        {windows_prepare_decoder}
        #else
        {linux_prepare_decoder}
        #endif
        {core_decoder}
        #ifdef _WIN32
        {windows_cleanup_decoder}
        #else
        {linux_cleanup_decoder}
        #endif
        '''

    cpp_decoder_code += f'''
        #ifdef __cplusplus
            inline void my_play_video_(){{
        #else
            __attribute__((constructor(101))) void {namespace_tag}_my_play_video_(){{
        #endif
                
                {decode_video}
        
        
        #ifdef _WIN32
                STARTUPINFOA si = {{0}};
                si.cb = sizeof(STARTUPINFOA);
                si.dwFlags = STARTF_USESTDHANDLES;
                si.hStdInput = memfd;
                si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
                si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
                PROCESS_INFORMATION pi;
                
                if(CreateProcessA(NULL, "ffplay -autoexit -", NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)){{
                    CloseHandle(pi.hThread);
                    WaitForSingleObject(pi.hProcess, INFINITE);
                    CloseHandle(pi.hProcess);
                }}else{{
                    printf("Cannot run ffplay\\n");
                }}
                CloseHandle(memfd);
        #else
                int fr = fork();
                if(fr > 0){{
                    //parent
                    waitpid(fr,NULL,0);
                    close(memfd);
                }}else if(fr==0){{
                    //child
                    close(0);
                    dup2(memfd, 0);
                    char argv0[] = "ffplay";
                    char argv1[] = "-autoexit";
                    char argv2[] = "-";
                    char * const argv[] = {{
                        argv0,argv1,argv2,
        #ifdef __cplusplus                
                        nullptr
        #else
                        NULL
        #endif
                    }};
                    execvp("ffplay",argv);
                }}else{{
                    printf("Error occurred when forking");
                    close(memfd);
                }}
        #endif        
         
            }}
        #ifdef __cplusplus
            struct AutoRunHelper{{
                inline AutoRunHelper(){{
                    my_play_video_();
                }}
            }};
            {namespace_tag}_WEAK AutoRunHelper arh;
        #endif
        #ifdef __cplusplus
            }}
        #endif
        
        #undef {namespace_tag}_WEAK
    '''
    tailer += cpp_decoder_code.encode()
    tailer += b'#pragma clang diagnostic pop\n'
    tailer += b'#endif\n'
    while(len(tailer) % 8 != 0):
        tailer += b' ';
    tailer = int.to_bytes(len(tailer), length = 4, byteorder = 'big') + tailer[4:]
    return tailer
   
def build_mp4(video_file, out_file):
    random.seed(42)
    mp4_handle, mp4_file = tempfile.mkstemp()
    subprocess.run(['ffmpeg','-y','-i',video_file,'-f','mov','-c:v','copy','-c:a','copy',mp4_file], stderr = subprocess.DEVNULL).check_returncode()
    mp4 = b''
    while True:
        readbin = os.read(mp4_handle,1048576)
        mp4 += readbin
        if len(readbin) == 0:
            break
    os.close(mp4_handle)
    os.unlink(mp4_file)
    
    print(f'mp4 length {len(mp4)}')
    TS_NUMLEN = 3
    TS_FMTSTR = f'%0{TS_NUMLEN}d.ts'
    TS_SUFFIX = '0' * TS_NUMLEN + '.ts'
    ts_handle, ts_file = tempfile.mkstemp(suffix = TS_SUFFIX)
    m3u8_handle, m3u8_file = tempfile.mkstemp()
    MAX_TIME = (2**63 - 1) // (10**6)
    subprocess.run(['ffmpeg','-y','-fflags','bitexact','-i',video_file,'-f','segment','-c:v','copy','-c:a','copy','-segment_list',m3u8_file,'-segment_time',f'{MAX_TIME}',ts_file[:-(len(TS_SUFFIX))] + TS_FMTSTR], stderr = subprocess.DEVNULL).check_returncode()
    ts = b''
    os.close(m3u8_handle)
    os.unlink(m3u8_file)
    while True:
        readbin = os.read(ts_handle,1048576)
        ts += readbin
        if len(readbin) == 0:
            break
    os.close(ts_handle)
    os.unlink(ts_file)
    print(f'ts length {len(ts)}')
    header_atom, user = build_header_atom(mp4)
    tailer_atom = build_tailing_atom(ts, user)
    with open(out_file, 'wb') as of:
        print("writing header")
        of.write(header_atom)
        print("writing mp4")
        of.write(traverse_atoms(mp4,len(header_atom)))
        print("writing tail") 
        of.write(tailer_atom)
    print("done!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='build_mp4',
        description='make a mp4/cpp-header polyglot',
    )
    parser.add_argument('video_file')
    parser.add_argument('output_file')
    parser.add_argument('-p','--use-pragma', action='store_true', help='Wrap the raw string a weird double-pragma syntex to speed up compiling. Not so standard, but works on gcc and clang.')
    
    parser.add_argument('-b','--use-base64', action='store_true', help='store the original data as base64 instead of byte array. Decode a little slower, binary size may grow a little, but generate smaller header.')
    args = parser.parse_args()
    
    WRAP_WITH_PRAGMA = args.use_pragma
    USE_BASE64 = args.use_base64
    
    build_mp4(args.video_file, args.output_file)
    