#include <stdarg.h>
#include <stdio.h>
namespace nkentseu { namespace platform { namespace detail {
inline int f(const char* fmt, ...) {
    char payload[1024];
    va_list args;
    __builtin_va_start(*reinterpret_cast<::__builtin_va_list*>(&args), fmt);
    const int payloadLen = vsnprintf(payload, sizeof(payload), fmt, args);
    __builtin_va_end(*reinterpret_cast<::__builtin_va_list*>(&args));
    return payloadLen;
}
}}}
