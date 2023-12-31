#include <stdio.h>
#include <stdlib.h>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#else
#include <unistd.h>
#endif

int main(){
	int rsize = 0;
	char buf[65536];
	FILE* writer = fopen(getenv("DUMP_FILE"), "wb");
#ifdef _WIN32
	_setmode( _fileno( stdin ), _O_BINARY );	
	while( 0 != (rsize = _read( _fileno( stdin ), buf, 65536 )) ){
#else
	while( 0 != (rsize = read( STDIN_FILENO, buf, 65536 )) ){
#endif
		fwrite(buf, 1, rsize, writer);
	}
	fclose(writer);
	return 0;
}

