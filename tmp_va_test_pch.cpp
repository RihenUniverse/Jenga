#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <stdarg.h>
#include <stdio.h>
namespace nkentseu { namespace platform { namespace detail {
inline int f(const char* fmt, ...) {
    char payload[1024];
    int payloadLen = 0;
    va_list args;
    va_start(args, fmt);
    payloadLen = vsnprintf(payload, sizeof(payload), fmt, args);
    va_end(args);
    return payloadLen;
}
}}}
