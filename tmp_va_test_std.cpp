#include <cstdarg>
#include <cstdio>
namespace nkentseu { namespace platform { namespace detail {
inline int f(const char* fmt, ...) {
    char payload[1024];
    std::va_list args;
    va_start(args, fmt);
    const int payloadLen = std::vsnprintf(payload, sizeof(payload), fmt, args);
    va_end(args);
    return payloadLen;
}
}}}
