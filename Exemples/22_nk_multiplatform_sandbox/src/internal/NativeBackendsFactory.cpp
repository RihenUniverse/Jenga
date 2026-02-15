#include "NativeBackends.hpp"

namespace nk::detail {

std::unique_ptr<IWindowBackend> CreateWindowBackend(PlatformBackend platform) {
    switch (platform) {
    case PlatformBackend::Win32: return CreateWin32WindowBackend();
    case PlatformBackend::Xcb: return CreateXcbWindowBackend();
    case PlatformBackend::Xlib: return CreateXlibWindowBackend();
    case PlatformBackend::Android: return CreateAndroidWindowBackend();
    case PlatformBackend::Emscripten: return CreateEmscriptenWindowBackend();
    case PlatformBackend::Ios: return CreateIosWindowBackend();
    case PlatformBackend::Macos: return CreateMacosWindowBackend();
    case PlatformBackend::Harmony: return CreateHarmonyWindowBackend();
    default: return CreateWin32WindowBackend();
    }
}

std::unique_ptr<IEventBackend> CreateEventBackend(PlatformBackend platform) {
    switch (platform) {
    case PlatformBackend::Win32: return CreateWin32EventBackend();
    case PlatformBackend::Xcb: return CreateXcbEventBackend();
    case PlatformBackend::Xlib: return CreateXlibEventBackend();
    case PlatformBackend::Android: return CreateAndroidEventBackend();
    case PlatformBackend::Emscripten: return CreateEmscriptenEventBackend();
    case PlatformBackend::Ios: return CreateIosEventBackend();
    case PlatformBackend::Macos: return CreateMacosEventBackend();
    case PlatformBackend::Harmony: return CreateHarmonyEventBackend();
    default: return CreateWin32EventBackend();
    }
}

} // namespace nk::detail
