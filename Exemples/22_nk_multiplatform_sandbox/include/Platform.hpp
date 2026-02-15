#pragma once

namespace nk {

enum class PlatformBackend {
    Win32,
    Xcb,
    Xlib,
    Android,
    Emscripten,
    Ios,
    Macos,
    Harmony,
    Unknown
};

const char* toString(PlatformBackend backend);
PlatformBackend detectPlatform();

} // namespace nk
