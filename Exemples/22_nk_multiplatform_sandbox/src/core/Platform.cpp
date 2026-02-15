#include "Platform.hpp"

#if defined(__APPLE__)
#include <TargetConditionals.h>
#endif

namespace nk {

PlatformBackend detectPlatform() {
#if defined(_WIN32)
    return PlatformBackend::Win32;
#elif defined(__EMSCRIPTEN__)
    return PlatformBackend::Emscripten;
#elif defined(__ANDROID__)
    return PlatformBackend::Android;
#elif defined(__OHOS__)
    return PlatformBackend::Harmony;
#elif defined(__APPLE__)
    #if TARGET_OS_IPHONE
        return PlatformBackend::Ios;
    #else
        return PlatformBackend::Macos;
    #endif
#elif defined(__linux__)
    return PlatformBackend::Xcb;
#else
    return PlatformBackend::Unknown;
#endif
}

const char* toString(PlatformBackend backend) {
    switch (backend) {
    case PlatformBackend::Win32: return "Win32";
    case PlatformBackend::Xcb: return "Xcb";
    case PlatformBackend::Xlib: return "Xlib";
    case PlatformBackend::Android: return "Android";
    case PlatformBackend::Emscripten: return "Emscripten";
    case PlatformBackend::Ios: return "iOS";
    case PlatformBackend::Macos: return "macOS";
    case PlatformBackend::Harmony: return "HarmonyOS";
    default: return "Unknown";
    }
}

} // namespace nk
