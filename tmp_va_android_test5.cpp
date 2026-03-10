#include <stdarg.h>
#include <stdio.h>
inline void f(const char* fmt, ...) {
    std::__va_list args;
    __builtin_va_start(args, fmt);
    (void)vsnprintf(nullptr, 0, fmt, args);
    __builtin_va_end(args);
}
int g(){ f("%d",1); return 0; }