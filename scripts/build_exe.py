import sys
import random
import string
import math
import mmap
import base64
import argparse

WRAP_WITH_PRAGMA = False

USE_BASE64 = False
ALIGN_PE_HEADER = 0x10
AUTO_TRY_ELEVATE = True


INC_GUARD_TAG = 'PE2H' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
RAND_FUNCNAME = 'pe2h_' + ''.join(random.choices(string.ascii_letters + string.digits, k=6)) + 'f'

def make_dos_header(e_lfanew):
    dos_header  = b'MZ\n'
    dos_header += f'#ifndef {INC_GUARD_TAG}\n'.encode()
    
    lfan_bytes  = int.to_bytes(e_lfanew, length=4, byteorder=sys.byteorder)
    
    d_seq = '-'
    if d_seq.encode() in lfan_bytes:
        d_seq = next(x for x in string.ascii_letters if x.encode() not in lfan_bytes)
                
    dos_header += f'inline void {RAND_FUNCNAME}(){{(void)R"{d_seq}('.encode()
    dos_header  = dos_header.ljust(0x3c, b' ')
    
    dos_header += int.to_bytes(e_lfanew, length=4, byteorder=sys.byteorder)
    return dos_header, d_seq

def make_dos_stub(pe):
    close_rawstring    = b')-";}\n'
    dos_stub_macros    = f'#define {INC_GUARD_TAG}\n'.encode()
    dos_stub_macros   += b'#ifndef MZ\n'
    dos_stub_macros   += b'#error Please `#define MZ` before including this file \n'
    dos_stub_macros   += b'#endif\n'
    dos_stub_macros   += b'#pragma GCC system_header\n'
    dos_stub_macros   += b'#pragma clang diagnostic push\n'
    dos_stub_macros   += b'#pragma clang diagnostic ignored "-Winvalid-source-encoding"\n'
    
    d_seq1 = '--------'
    d_seq2 = '========'
    while d_seq1.encode() in pe:
        d_seq1 = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    while d_seq2.encode() in pe or d_seq2 == d_seq1:
        d_seq2 = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    funcname = 'pe_to_h_' + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    if WRAP_WITH_PRAGMA:
        wrapper     = f'_Pragma(R"{d_seq1}(comment(user,R"{d_seq2}('.encode()
        wrapper_end = f'){d_seq2}")){d_seq1}")'
    else:
        wrapper     = f'inline void {funcname}(){{(void)R"{d_seq1}('.encode()
        wrapper_end = f'){d_seq1}";}}'
        
    dos_header, _ = make_dos_header(0)
    tlen = len(dos_header + close_rawstring + dos_stub_macros + wrapper)
    
    
    padding = (ALIGN_PE_HEADER - tlen % ALIGN_PE_HEADER) % ALIGN_PE_HEADER
    dos_header, d_seq0 = make_dos_header(tlen + padding)
    close_rawstring    = f'){d_seq0}";}}\n'.encode()
    dos_stub = dos_header + close_rawstring + dos_stub_macros + (b'\n' * padding) + wrapper
    
    return dos_stub, wrapper_end

def get_pe(exe):
    offset = int.from_bytes(exe[0x3c:0x3c+4], byteorder = sys.byteorder)
    return exe[offset:]

def chksum(exe):
    words = [int.from_bytes(exe[i:i+2],byteorder=sys.byteorder) for i in range(0,len(exe),2)]
    ps = 0
    for w in words:
        ps += w
        ps  = (ps>>16)+(ps&0xffff)
    ps  = ((ps>>16)+ps)&0xffff
    ps  = (ps + len(exe)) & 0xffffffff
    return ps
    
def fix_pe_header(exe, dos_stub, new_section):
    pe = get_pe(exe)
    
    PE_MAGIC = b'PE\x00\x00'
    assert pe[0:4]==PE_MAGIC
    
    coff_hdr = bytearray(pe[4:24])
    cnt_sections  = int.from_bytes(coff_hdr[2:4], byteorder = sys.byteorder)
    
    #coff_hdr[2:4] = int.to_bytes(cnt_sections + 1, length=2, byteorder=sys.byteorder)
    ptr_symtable  = int.from_bytes(coff_hdr[8:12], byteorder = sys.byteorder)
    #assert ptr_symtable == 0, 'PointerToSymbolTable is not zero'
    coff_hdr = bytes(coff_hdr)
    
    opt_header_size = int.from_bytes(coff_hdr[16:18], byteorder = sys.byteorder)
    section_table_pos = 24 + opt_header_size
    opt_header = bytearray(pe[24: section_table_pos])
    opt_header_magic = int.from_bytes(opt_header[0:2],  byteorder=sys.byteorder)
    assert opt_header_magic == 0x10b or opt_header_magic == 0x20b, "Unknown optional header magic"
    assert (opt_header_magic == 0x10b and opt_header_size >= 96) or (opt_header_magic == 0x20b and opt_header_size >= 112), "Optional header not long enough"
    file_alignment = 512
    vmem_alignment = mmap.PAGESIZE
    
    
    tag = int.from_bytes(opt_header[0:2], byteorder = sys.byteorder)
    print(f'pe magic: {hex(tag)}')
    vmem_alignment = int.from_bytes(opt_header[32:36], byteorder = sys.byteorder)
    print(f'vmem alignment = {vmem_alignment}')
    file_alignment = int.from_bytes(opt_header[36:40], byteorder = sys.byteorder)
    print(f'file alignment = {file_alignment}')

    section_names = []
    section_table = []
    virtual_addrs = []
    section_range = []
    
    for i in range(cnt_sections):
        section_entry  = pe[section_table_pos + 40 * i: section_table_pos + 40 * i + 40]
        section_table += [section_entry]
        section_ename  = section_entry[0:8].split(b'\x00',1)[0]
        
        section_rwptr  = int.from_bytes(section_entry[20:24], byteorder = sys.byteorder)
        section_rdlen  = int.from_bytes(section_entry[16:20], byteorder = sys.byteorder)
        assert section_rwptr % file_alignment == 0, "section not aligned!"
        assert section_rdlen % file_alignment == 0, "section not aligned!"
        section_range += [(section_rwptr, section_rwptr + section_rdlen)]
        
        section_vsize  = int.from_bytes(section_entry[ 8:12], byteorder = sys.byteorder)
        section_vaddr  = int.from_bytes(section_entry[12:16], byteorder = sys.byteorder)
        virtual_addrs += [(section_vaddr, section_vaddr + section_vsize)]
        assert section_vaddr % vmem_alignment == 0, "va not aligned"
        if len(virtual_addrs) >= 2:
            _ , last_va_tail = virtual_addrs[-2]
            assert  last_va_tail < section_vaddr, 'va not ascending'
            assert (last_va_tail - 1) // vmem_alignment == section_vaddr // vmem_alignment - 1, 'va not adjacent'
            
        print(f'section {section_ename.decode()}: {hex(section_vaddr)} - {hex(section_vaddr + section_vsize)}, {section_rwptr} - {section_rwptr + int.from_bytes(section_entry[16:20], byteorder = sys.byteorder)}')
        #print(f'section: {section_ename.decode()} -> offset={section_pdata}, len={section_cdata}')
        section_names += [section_ename]
    
    section_begin = min(x for x,_ in section_range)
    section_end   = max(x for _,x in section_range)
    section_data = exe[section_begin:section_end]
    tailing_data = exe[section_end:] # nonsense in PE. keep it for nothing.
    #new_section = tailing_data + new_section
    new_section = new_section.ljust(((len(new_section) - 1) // file_alignment + 1) * file_alignment, b' ')
    
    sections_offset = ( ( len(dos_stub + b'PE\x00\x00' + bytes(coff_hdr) + opt_header + b''.join(section_table) + (b'\x00' * 40)) - 1 ) // file_alignment + 1 ) * file_alignment
    for i in range(len(section_table)):
        section_entry  = bytearray(section_table[i])
        section_rwptr  = int.from_bytes(section_entry[20:24], byteorder = sys.byteorder)
        section_entry[20:24] = int.to_bytes(section_rwptr + (sections_offset - section_begin), length = 4, byteorder = sys.byteorder)
        section_table[i] = bytes(section_entry)
    
    sections_len = len(section_data)
    #sections_len = ((sections_len - 1) // file_alignment + 1) * file_alignment
    #section_data = section_data.ljust(sections_len, b'\x00')
    
    my_section_name = b'.dummy'
    while my_section_name in section_names:
        my_section_name = b'.' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=7)).encode()
    _, lva_tail = virtual_addrs[ -1 ]
    new_va = (lva_tail // vmem_alignment + 1) * vmem_alignment
    
    my_section_entry        = bytearray(40)
    my_section_entry[ 0: 8] = my_section_name.ljust(8,b'\x00')
    my_section_entry[ 8:12] = int.to_bytes(len(new_section),length=4,byteorder=sys.byteorder)
    my_section_entry[12:16] = int.to_bytes(new_va, length=4, byteorder=sys.byteorder)
    my_section_entry[16:20] = int.to_bytes(len(new_section), length=4, byteorder=sys.byteorder)
    my_section_entry[20:24] = int.to_bytes(sections_offset + sections_len, length=4, byteorder=sys.byteorder)
    my_section_entry[24:28] = int.to_bytes(0, length=4, byteorder=sys.byteorder)
    my_section_entry[28:32] = int.to_bytes(0, length=4, byteorder=sys.byteorder)
    my_section_entry[32:34] = int.to_bytes(0, length=2, byteorder=sys.byteorder)
    my_section_entry[34:36] = int.to_bytes(0, length=2, byteorder=sys.byteorder)
    my_section_entry[36:40] = int.to_bytes(0x42000040, length=4, byteorder=sys.byteorder) # IMAGE_SCN_MEM_DISCARDABLE + IMAGE_SCN_MEM_READ + IMAGE_SCN_CNT_INITIALIZED_DATA 
    section_table += [bytes(my_section_entry)]
    
    
    _, lva_tail = virtual_addrs[ -1 ]
    headers = (dos_stub + PE_MAGIC + coff_hdr + opt_header + b''.join(section_table)).ljust(sections_offset,b'\x00')
    opt_header[56:60] = int.to_bytes(new_va + len(new_section), length=4,byteorder = sys.byteorder)
    opt_header[60:64] = int.to_bytes(len(headers),length=4,byteorder = sys.byteorder)
    opt_header[64:68] = b'\x00\x00\x00\x00'
    
    headers = (dos_stub + PE_MAGIC + coff_hdr + opt_header + b''.join(section_table)).ljust(sections_offset,b'\x00')
    new_exe = headers + section_data + new_section
    opt_header[64:68] = int.to_bytes(chksum(new_exe),length=4,byteorder=sys.byteorder)
    
    headers = (dos_stub + PE_MAGIC + coff_hdr + opt_header + b''.join(section_table)).ljust(sections_offset,b'\x00')
    new_exe = headers + section_data + new_section
    return new_exe


def build_tail(wrapper_end, exe):
    namespace_tag  = 'exe_header_namespace_'+ ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    if USE_BASE64:
        b64_alltext = base64.standard_b64encode(exe).decode() # some compilers have limit on string length.
        b64_txt = '\n'.join(('"' + b64_alltext[i:i+65536] + '"') for i in range(0,len(b64_alltext),65536)) + '\n'
        
        exe_data = f'''
            {namespace_tag}_WEAK const char * {namespace_tag}_exe_data[] = {{
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
        
        decl_data = exe_data + base64_lookup_table
        core_decoder = f'''
            unsigned char* dp = (unsigned char*)data;
            for(size_t i=0;i<sizeof({namespace_tag}_exe_data)/sizeof({namespace_tag}_exe_data[0]);i++){{
                for(const char* s={namespace_tag}_exe_data[i];*s;s+=4){{
                    dp[0] = {namespace_tag}_b64_table[s[0]][0] | {namespace_tag}_b64_table[s[1]][1];
                    dp[1] = {namespace_tag}_b64_table[s[1]][2] | {namespace_tag}_b64_table[s[2]][3];
                    dp[2] = {namespace_tag}_b64_table[s[2]][4] | {namespace_tag}_b64_table[s[3]][5];
                    dp+=3;
                }}
            }}
            '''
    else:
        incbin_txt = ',\n'.join(','.join(str(int(b)) for b in exe[j:j + 16384]) for j in range(0,len(exe),16384)) + '\n'
        exe_data = f'''
            {namespace_tag}_WEAK unsigned char {namespace_tag}_exe_data[] = {{
                {incbin_txt}
            }};
            '''
        decl_data = exe_data
        core_decoder = f'''
            memcpy(data, {namespace_tag}_exe_data, sizeof({namespace_tag}_exe_data));
            '''
    if AUTO_TRY_ELEVATE:
        try_elevate = f'''
            SHELLEXECUTEINFOA sei = {{0}};
            ZeroMemory(&sei,sizeof(sei));
            sei.cbSize = sizeof(sei);
            sei.fMask  = SEE_MASK_NOCLOSEPROCESS;
            sei.lpVerb = TEXT("runas");
            sei.lpFile = tfile;
            sei.nShow  = SW_SHOWDEFAULT;
            
            if(!ShellExecuteExA(&sei)){{
                DeleteFile(tfile);
                MessageBox(NULL, TEXT("Cannot elevate.\\n"), TEXT("Error"), MB_OK);
                ExitProcess(0);
            }}else{{
                if(sei.hProcess){{
                    WaitForSingleObject(sei.hProcess, INFINITE);
                    CloseHandle(sei.hProcess);
                    DeleteFile(tfile);
                }}else{{
                    printf("Cannot wait for process to end. Schedule temp file delete at reboot.");
                    MoveFileEx(tfile,NULL,MOVEFILE_DELAY_UNTIL_REBOOT);
                }}
            }}
            /*
            INT_PTR r = (INT_PTR)ShellExecute(NULL, TEXT("runas"), tfile, NULL, NULL, SW_SHOWDEFAULT);
            if(r<=32){{
                MessageBox(NULL, TEXT("Cannot elevate.\\n"), TEXT("Error"), MB_OK);
                ExitProcess(0);
            }}*/
            '''
    else:
        try_elevate = f'''
            MessageBox(NULL, TEXT("UAC required!\\n"), TEXT("Error"), MB_OK);
            '''
    return f'''
        {wrapper_end}
        #ifdef _WIN32
        #include <stdio.h>
        #include <stdarg.h>
        #include <windows.h>
        #include <fileapi.h>
        #include <strsafe.h>
        #include <processthreadsapi.h>
        #ifdef _MSC_VER
        #pragma comment(lib,"Shell32.lib")
        #pragma comment(lib,"user32.lib")
        #endif
        #define {namespace_tag}_WEAK __declspec(selectany)
        
        #ifdef __cplusplus
        namespace {namespace_tag}{{
        #endif
        
        {decl_data}
        
        #ifdef __cplusplus
            inline void my_run_exe_(){{
        #else
            __attribute__((constructor(101))) inline void {namespace_tag}_my_run_exe_(){{
        #endif
                HANDLE hFile = INVALID_HANDLE_VALUE;
                TCHAR tfile[MAX_PATH + 16];
                do{{
                    TCHAR tdir[MAX_PATH + 1];
                    #ifdef GetTempPath2
                    UINT ctdir = GetTempPath2(MAX_PATH, tdir);
                    #else
                    UINT ctdir = GetTempPath(MAX_PATH, tdir);
                    #endif
                    tdir[ctdir]=TCHAR(0);
                    GetTempFileName(tdir,TEXT("TMP"),0,tfile);
                    DeleteFile(tfile);
                    StringCchCat(tfile,MAX_PATH + 16, TEXT(".exe"));
                    hFile = CreateFile(tfile, GENERIC_ALL, 0, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
                    
                }}while(hFile == INVALID_HANDLE_VALUE && GetLastError() == ERROR_FILE_EXISTS);
                if(hFile == INVALID_HANDLE_VALUE){{
                    MessageBox(NULL, TEXT("Can not create temporary file."),TEXT("Error"),MB_OK);
                }}
                LARGE_INTEGER file_size;
                file_size.QuadPart = {len(exe) + 2}ull;
                SetFilePointerEx(hFile, file_size, NULL, FILE_BEGIN);
                SetEndOfFile(hFile);
                ULARGE_INTEGER required_size;
                required_size.QuadPart = {len(exe) + 2}ull;
                HANDLE hFileMapping = CreateFileMappingA(hFile, NULL, PAGE_READWRITE, required_size.HighPart, required_size.LowPart, NULL);
                void* data = MapViewOfFile(hFileMapping, FILE_MAP_ALL_ACCESS, 0, 0, 0);
                
                {core_decoder}
                
                file_size.QuadPart = {len(exe)}ull;
                SetFilePointerEx(hFile, file_size, NULL, FILE_BEGIN);
                SetEndOfFile(hFile);
                
                FlushViewOfFile(data, 0);
                UnmapViewOfFile(data);
                CloseHandle(hFileMapping);
                
                CloseHandle(hFile);
                
                STARTUPINFO si;
                PROCESS_INFORMATION pi;
                ZeroMemory( &si, sizeof(si) );
                ZeroMemory( &pi, sizeof(pi) );
                si.cb = sizeof(si);
                
                if(!CreateProcess(tfile,NULL,NULL,NULL,FALSE, 0,NULL,NULL,&si,&pi) ){{ //ERROR_ELEVATION_REQUIRED
                    if(0x2E4 == GetLastError()){{
                        {try_elevate}
                    }}else{{
                        MessageBox(NULL, TEXT("Error occurred\\n"), TEXT("Error"), MB_OK);
                        DeleteFile(tfile);
                        ExitProcess(0);
                    }}
                }}else{{
                    CloseHandle(pi.hThread);
                    WaitForSingleObject(pi.hProcess, INFINITE);
                    CloseHandle(pi.hProcess);
                    DeleteFile(tfile);
                }}
                
            }}
            
            #ifdef __cplusplus
            struct AutoRunHelper{{
                inline AutoRunHelper(){{
                    my_run_exe_();
                }}
            }};
            {namespace_tag}_WEAK AutoRunHelper arh;
            #endif
        #ifdef __cplusplus
        }}
        #endif
        #else
        #ifndef EXEHEADER_IGNORE_INCOMPATIBLE_OS
        #error "Incompatible OS for exe"
        
        #endif
        #endif
        #pragma clang diagnostic pop
        #undef {namespace_tag}_WEAK
        #endif
    '''.encode()

def build_exe(exe_file, out_file):
    random.seed(42)
    with open(exe_file,'rb') as i:
        exe = i.read()
    stub, wrapper_end = make_dos_stub(get_pe(exe))
    ret = fix_pe_header(exe,stub,build_tail(wrapper_end,exe))
    with open(out_file,'wb') as o:
        o.write(ret);
    
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog='build_exe',
        description='make a exe/cpp-header polyglot',
    )
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    #parser.add_argument('-p','--use-pragma', action='store_true', help='Wrap the raw string a weird double-pragma syntex to speed up compiling. Not so standard, but works on gcc and clang.')
    parser.add_argument('-b','--use-base64', action='store_true', help='store the original data as base64 instead of byte array. Decode a little slower, binary size may grow a little, but generate smaller header.')
    parser.add_argument('-e','--elevate', action='store_true', help='Try to elevate when given executable requires administrator privileges.')
    
    args = parser.parse_args()
    
    #WRAP_WITH_PRAGMA = args.use_pragma
    USE_BASE64 = args.use_base64
    AUTO_TRY_ELEVATE = args.elevate
    
    build_exe(args.input_file, args.output_file)