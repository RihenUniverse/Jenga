#include <cstdarg>
#include <cstdio>
int f(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int n = vsnprintf(nullptr, 0, fmt, args);
    va_end(args);
    return n;
}