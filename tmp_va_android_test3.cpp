#include <stdarg.h>
#include <stdio.h>
int f(const char* fmt, ...) {
    __builtin_va_list args;
    __builtin_va_start(args, fmt);
    int n = vsnprintf(nullptr, 0, fmt, args);
    __builtin_va_end(args);
    return n;
}