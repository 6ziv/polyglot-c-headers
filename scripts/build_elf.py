import sys
import random
import string
import base64
import argparse

PIPE_SCRIPT = False

def make_script_header(skip, blen, dlen, script_shebang = None):
    skip_txt = str(skip).ljust(8,' ')
    blen_txt = str(blen).ljust(16,' ')
    dlen_txt = str(dlen).ljust(16,' ')
    if PIPE_SCRIPT and script_shebang is not None:
        dd_cmd = f'dd bs={dlen_txt} count=1 iflag=fullblock status=none| {script_shebang};'
        exec_cmd = ''
    else:
        dd_cmd = f'dd of="$tmp" bs={dlen_txt} count=1 iflag=fullblock status=none;'
        if script_shebang is None:
            exec_cmd = f'exec "$tmp"'
        else:
            exec_cmd = f'exec {script_shebang} "$tmp" $@'
    script = f'''
        #if 0
        tmp=$(mktemp -q --tmpdir=/tmp)
        if [ $? -ne 0 ]; then
            echo cannot create temporary file
            exit 1
        fi
        chmod 700 "$tmp"
        me="$(command -v "$0")"
        
        dd if="$me" bs=64M status=none| {{ dd of="/dev/null" bs={skip_txt} count=1 status=none; dd bs={blen_txt} count=1 iflag=fullblock status=none| base64 -d -i| {dd_cmd} }}
        if [ $? -ne 0 ]; then
            echo cannot copy to temporary file
            exit 1
        fi
        
        {exec_cmd}
        if [ $? -ne 0 ]; then
            echo execute extracted file
            exit 1
        fi
        
        exit 0
        #endif
        '''
    return script

def make_c_header(elf, script_shebang = None, manually_cmdline = None):
    inc_guard = 'ELF_AS_HEADER_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    namespace_tag  = 'elfheader_namespace_'+ ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    decoder_header = f'''
        #pragma once
        #ifndef {inc_guard}
        #define {inc_guard}
        #pragma GCC system_header
        #include <stdio.h>
        #include <stdlib.h>
        #ifdef __linux__
        #define _GNU_SOURCE
        #include <sys/mman.h>
        #include <sys/wait.h>
        #include <unistd.h>
        #include <sys/types.h>
        extern char ** environ;
        #define {namespace_tag}_WEAK __attribute__((weak))
        #ifdef __cplusplus
        namespace {namespace_tag}{{
        #endif
            {namespace_tag}_WEAK const char* {namespace_tag}_elf_data[] = {{
        
        '''
    b64_oneline = base64.standard_b64encode(elf).decode() # some compilers have limit on string length.
    b64_txt  = '"' + '",\n"'.join(b64_oneline[i:i+65536] for i in range(0, len(b64_oneline),65536)) + '"\n'
    decoder  = make_script_header(0, 0, 0, script_shebang) + decoder_header
    decoder  = make_script_header(len(decoder), len(b64_txt), len(elf), script_shebang) + decoder_header + b64_txt;
    decoder += f'''
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
    
    if manually_cmdline is None:
        run_args = [('"tmp_prog"', False), ('nullptr', True)]
        use_memfile = True
    else:
        NULL_STR = '''
            
            #ifdef __cplusplus   
            nullptr
            #else
            NULL
            #endif
            
            '''
        run_args = [('tfn', True) if x == '@file@' else (x, False) for x in manually_cmdline] + [(NULL_STR, True)]
        use_memfile = False
    
    if use_memfile:
        create_tmpfile = 'int memfd = memfd_create("elf_2_run", 0);'
        close_tmpfile = 'close(memfd);'
    else:
        tfn_prefix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        create_tmpfile = f'''
            char tfn[] = "/tmp/{tfn_prefix}XXXXXX";
            int memfd = mkstemp(tfn);
            '''
        close_tmpfile = f'''
            close(memfd);
            unlink(tfn);
            '''
    decl_argv  = '\n'.join([f'char* argv{idx} = {arg};' if isvar else f'char argv{idx}[] = {arg};' for idx, (arg, isvar) in enumerate(run_args)]) + '\n'
    decl_argv += 'char * const argv[] = {' + ','.join([f'argv{i}' for i in range(len(run_args))]) + '};\n'
    if manually_cmdline is None:
        run_cmd  = f'''
            fexecve(memfd, argv, environ);
            '''
    else:
        run_cmd  = f'''
            execve({manually_cmdline[0]}, argv, environ);
            '''
    decoder += f'''
        {base64_lookup_table}
        #ifdef __cplusplus
            inline void my_run_elf_(){{
        #else
            __attribute__((constructor(101))) void {namespace_tag}_my_run_elf_(){{
        #endif
                {create_tmpfile}
                ftruncate(memfd, {len(elf) + 2});
                void* data = mmap(NULL, {len(elf) + 2}, PROT_READ|PROT_WRITE, MAP_SHARED, memfd, 0);

                unsigned char* dp = (unsigned char*)data;
                for(size_t i=0;i<sizeof({namespace_tag}_elf_data)/sizeof({namespace_tag}_elf_data[0]);i++){{
                    for(const char* s={namespace_tag}_elf_data[i];*s;s+=4){{
                        dp[0] = {namespace_tag}_b64_table[s[0]][0] | {namespace_tag}_b64_table[s[1]][1];
                        dp[1] = {namespace_tag}_b64_table[s[1]][2] | {namespace_tag}_b64_table[s[2]][3];
                        dp[2] = {namespace_tag}_b64_table[s[2]][4] | {namespace_tag}_b64_table[s[3]][5];
                        dp+=3;
                    }}
                }}
                msync(data,{len(elf) + 2},MS_SYNC);
                munmap(data,{len(elf) + 2});
                ftruncate(memfd, {len(elf)});
                int fr = fork();
                if(fr>0){{//parent
                    waitpid(fr,NULL,0);
                    {close_tmpfile}
                }}else if(fr==0){{
                    {decl_argv}
                    {run_cmd}
                }}else{{
                    printf("Error occurred when forking");
                    {close_tmpfile}
                }}
            }}
            
        #ifdef __cplusplus
            struct AutoRunHelper{{
                inline AutoRunHelper(){{
                    my_run_elf_();
                }}
            }};
            {namespace_tag}_WEAK AutoRunHelper arh __attribute__ ((weak));
        #endif
        
        #ifdef __cplusplus
            }}
        #endif
        #undef {namespace_tag}_WEAK
        
        #else 
        #ifndef ELF_HEADER_IGNORE_INCOMPATIBLE_OS
        #error "Incompatible OS for elf"
        #endif
        #endif //linux
        
        #endif
        '''
    return decoder
    
def build_elf(elf_file, out_file, shebang, manually_cmdline):
    random.seed(42)
    with open(elf_file, 'rb') as ifile, open(out_file, 'w') as ofile:
        in_data = ifile.read()
        if manually_cmdline is not None:
            cmdline = ['@file@' if s == '@file@' else f'"{s.encode("unicode_escape").decode()}"' for s in manually_cmdline]
        else:
            cmdline = None
        ofile.write(make_c_header(in_data, shebang, cmdline))
        '''    
        if manually_cmdline is not None:
            ofile.write(make_c_header(in_data, 'ffplay', ['"/bin/env"','"ffplay", '@file@'']))
            
        elif in_data[0: 4] == b'\x7fELF':
            print("input file seems to be ELF")
            ofile.write(make_c_header(in_data))
        else:
            print("input file is not ELF. considered a shell script.")
            if in_data[0:2] == b'#!':
                shebang_line = in_data.split(b'\n')[0][2:].strip().decode()
            else:
                shebang_line = '/usr/bin/env sh'
                in_data = '#!/usr/bin/env sh\n' + in_data
            ofile.write(make_c_header(in_data, shebang_line))
        '''

if __name__=='__main__':
    parser = argparse.ArgumentParser(
        prog='build_elf',
        description='make a elf/cpp-header or bash-script/cpp-header polyglot',
    )
    parser.add_argument('input_file')
    parser.add_argument('output_file')
    parser.add_argument('-p','--use-pipe', action='store_true', help='when decoding a script with a shebang line, send it to the interpreter directly through a pipe.')
    parser.add_argument('-s','--shebang', type=str, help='manually assign a shebang string. the generated script uses this to run open the decoded content. if none, exec the decoded binary')
    parser.add_argument('-c','--cmdline', type=str, nargs=argparse.REMAINDER, help='manually assign a command line which the executable will pass to execve (first element will be passed as pathname). use \'@path@\' to represent the decoded file path. if none, execute the decoded binary.')

    args = parser.parse_args()
    PIPE_SCRIPT = args.use_pipe
    build_elf(args.input_file, args.output_file, args.shebang, args.cmdline)
            
    '''
    with open(in_file, 'rb') as ifile, open(out_file, 'w') as ofile:
        in_data = ifile.read()
        ofile.write(make_c_header(in_data, 'ffplay', ['"/bin/env"','"ffplay", '@file'']))
    '''
        