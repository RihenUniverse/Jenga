# Example 24 — All Platforms Build

Build the same project for every platform Jenga supports, from a single `.jenga` file.

## Supported Platforms

| Platform | Toolchain        | Output           |
|----------|-----------------|------------------|
| Windows  | Clang / MSVC    | `.exe`           |
| Linux    | Clang cross     | ELF binary       |
| Android  | Android NDK     | `.apk`           |
| Web      | Emscripten      | `.html` + `.wasm`|
| macOS    | Apple Clang     | Mach-O binary    |
| iOS      | Apple Clang     | `.ipa`           |

## Usage

```bash
# Build for host platform (Windows)
jenga build

# Build for ALL platforms at once
jenga build --platform jengaall

# Target a specific platform
jenga build --platform android
jenga build --platform web
jenga build --platform linux

# Release build
jenga build --config Release
```

## Prerequisites

- **Windows**: Clang or MSVC installed
- **Linux cross**: Clang with Linux sysroot
- **Android**: `ANDROID_SDK_ROOT` and `ANDROID_NDK_ROOT` set
- **Web**: Emscripten SDK installed (`emsdk`)
- **macOS/iOS**: macOS with Xcode (uncomment in `.jenga`)
