#include <stdarg.h>
#include <stdio.h>
int f(const char* fmt, ...) {
    char b[16];
    int n=0;
    va_list args;
    va_start(args, fmt);
    n = vsnprintf(b, sizeof(b), fmt, args);
    va_end(args);
    return n;
}
