#include "zlib.h"
#include <stdio.h>

int main(int argc, char *argv[]){
    printf("%s: using zlib: %s\n", argv[0], zlibVersion());
    return 0;
}

