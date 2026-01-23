# Cross-Platform Build Guide
## Building for Multiple Platforms with Nken

Nken supports building C/C++ projects for **all major platforms** from a single configuration file.

## Table of Contents
1. [Platform Overview](#platform-overview)
2. [Toolchain Setup](#toolchain-setup)
3. [Project Configuration](#project-configuration)
4. [Build Commands](#build-commands)
5. [Platform-Specific Notes](#platform-specific-notes)

---

## Platform Overview

### Supported Platforms

| Platform | Architecture | Use Case |
|----------|--------------|----------|
| **Windows** | x86, x64, ARM64 | Desktop applications |
| **Linux** | x86_64, ARM64 | Desktop/Server applications |
| **MacOS** | x86_64, ARM64 (Apple Silicon) | Desktop applications |
| **Android** | ARM, ARM64, x86, x86_64 | Mobile applications |
| **iOS** | ARM64 | Mobile applications (iPhone/iPad) |
| **Emscripten** | WebAssembly | Web applications |

### Platform Detection

Nken automatically detects your current platform:
```bash
nken build  # Auto-detects: Linux, Windows, or MacOS
```

### Cross-Compilation

Specify target platform explicitly:
```bash
nken build --platform Android
nken build --platform iOS
nken build --platform Emscripten
```

---

## Toolchain Setup

### 1. Windows

**Option A: MSVC (Visual Studio)**
- Install Visual Studio 2019+ with C++ workload
- Toolchain: `msvc`
- Compiler: `cl.exe`

```python
with toolchain("msvc", "cl"):
    cppcompiler("cl.exe")
    ccompiler("cl.exe")
```

**Option B: MinGW-w64**
- Download from: https://mingw-w64.org
- Toolchain: `gcc`
- Compiler: `g++.exe`

### 2. Linux

**GCC (Default)**
```bash
sudo apt-get install build-essential  # Ubuntu/Debian
sudo yum groupinstall "Development Tools"  # CentOS/RHEL
```

```python
with toolchain("gcc", "g++"):
    cppcompiler("/usr/bin/g++")
    ccompiler("/usr/bin/gcc")
```

**Clang (Alternative)**
```bash
sudo apt-get install clang
```

### 3. macOS

**Xcode Command Line Tools**
```bash
xcode-select --install
```

```python
with toolchain("clang", "clang++"):
    cppcompiler("/usr/bin/clang++")
    ccompiler("/usr/bin/clang")
```

### 4. Android

**Android NDK**
1. Download NDK: https://developer.android.com/ndk/downloads
2. Set environment variable:
   ```bash
   export ANDROID_NDK_ROOT=/path/to/ndk
   ```

```python
with toolchain("android", "clang++"):
    toolchaindir("$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64")

with project("MyApp"):
    # Android settings
    with filter("system:Android"):
        usetoolchain("android")
        androidminsdk(21)
        androidtargetsdk(33)
```

**Build Command:**
```bash
nken build --platform Android --toolchain android
```

### 5. iOS

**Xcode**
- Install Xcode from App Store
- Install iOS SDK

```python
with toolchain("ios", "clang++"):
    toolchaindir("/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain")

with filter("system:iOS"):
    usetoolchain("ios")
    defines(["TARGET_OS_IPHONE"])
```

**Note:** iOS builds must be done on macOS

### 6. Emscripten (WebAssembly)

**EMSDK Installation**
```bash
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh
```

```python
with toolchain("emscripten", "em++"):
    cppcompiler("em++")
    ccompiler("emcc")

with filter("system:Emscripten"):
    usetoolchain("emscripten")
```

**Build Command:**
```bash
source /path/to/emsdk_env.sh
nken build --platform Emscripten --toolchain emscripten
```

---

## Project Configuration

### Basic Multi-Platform Project

```python
with workspace("MyApp"):
    configurations(["Debug", "Release"])
    platforms(["Windows", "Linux", "MacOS", "Android", "iOS", "Emscripten"])
    
    # Define toolchains for each platform
    with toolchain("msvc", "cl"):
        pass
    
    with toolchain("gcc", "g++"):
        pass
    
    with toolchain("clang", "clang++"):
        pass
    
    with toolchain("android", "clang++"):
        pass
    
    with toolchain("ios", "clang++"):
        pass
    
    with toolchain("emscripten", "em++"):
        pass
    
    # Cross-platform library
    with project("Core"):
        staticlib()
        language("C++")
        cppdialect("C++20")
        
        location(".")
        
        files([
            "/Core/src/**.cpp",
            "/Core/src/**.h"
        ])
        
        includedirs(["/Core/include"])
        
        targetdir("%{wks.location}/Build/%{cfg.platform}/%{cfg.buildcfg}/Lib")
        
        # Platform-specific settings
        with filter("system:Windows"):
            usetoolchain("msvc")
            defines(["PLATFORM_WINDOWS"])
        
        with filter("system:Linux"):
            usetoolchain("gcc")
            defines(["PLATFORM_LINUX"])
        
        with filter("system:MacOS"):
            usetoolchain("clang")
            defines(["PLATFORM_MACOS"])
        
        with filter("system:Android"):
            usetoolchain("android")
            defines(["PLATFORM_ANDROID"])
        
        with filter("system:iOS"):
            usetoolchain("ios")
            defines(["PLATFORM_IOS"])
        
        with filter("system:Emscripten"):
            usetoolchain("emscripten")
            defines(["PLATFORM_WEB"])
```

### Project Location Handling

```python
with project("Logger"):
    location(".")  # Default: workspace location
    
    # Files relative to project location
    files([
        "/src/**.cpp",  # = ./src/**.cpp relative to Logger location
        "/include/**.h"
    ])
    
    # Absolute paths
    files([
        "%{wks.location}/Logger/src/**.cpp"
    ])
    
    # Object dir relative to workspace
    objdir("%{wks.location}/Build/Obj/%{cfg.buildcfg}/%{prj.name}")
```

---

## Build Commands

### Native Build (Auto-Detect)
```bash
nken build                    # Detects current platform
nken build --config Release   # Release build
nken build --jobs 8          # Parallel build with 8 jobs
```

### Cross-Platform Builds

**Windows Target:**
```bash
nken build --platform Windows --toolchain msvc
nken build --platform Windows --toolchain gcc  # MinGW
```

**Linux Target:**
```bash
nken build --platform Linux --toolchain gcc
nken build --platform Linux --toolchain clang
```

**macOS Target:**
```bash
nken build --platform MacOS --toolchain clang
```

**Android Target:**
```bash
nken build --platform Android --toolchain android
nken build --platform Android --toolchain android --config Release

# With signing
nken build --platform Android --config Release
```

**iOS Target:**
```bash
nken build --platform iOS --toolchain ios
nken build --platform iOS --config Release
```

**WebAssembly Target:**
```bash
source /path/to/emsdk_env.sh
nken build --platform Emscripten --toolchain emscripten
```

### Other Commands
```bash
nken clean                        # Clean all platforms
nken rebuild --platform Android   # Clean + build
nken run --config Release         # Run (native platform only)
nken info                         # Show configuration
nken gen --ide vscode            # Generate IDE configs
```

---

## Platform-Specific Notes

### Windows

**Executable Types:**
- `consoleapp()` → Console application (.exe)
- `windowedapp()` → Windows GUI application (.exe)

**System Libraries:**
```python
with filter("system:Windows"):
    links(["kernel32", "user32", "gdi32", "shell32"])
```

**Resources:**
```python
with filter("system:Windows"):
    embedresources([
        "resources/app.ico",
        "resources/app.rc"
    ])
```

### Linux

**System Libraries:**
```python
with filter("system:Linux"):
    links(["pthread", "dl", "m", "X11"])
```

**Shared Libraries:**
- Automatically get `lib` prefix: `libCore.so`
- Copy dependencies: DLLs auto-copied

### macOS

**App Bundles:**
```python
with filter("system:MacOS"):
    windowedapp()  # Creates .app bundle
    
    postbuild([
        "mkdir -p %{prj.targetdir}/MyApp.app/Contents/MacOS",
        "cp %{prj.targetdir}/MyApp %{prj.targetdir}/MyApp.app/Contents/MacOS/"
    ])
```

**Frameworks:**
```python
with filter("system:MacOS"):
    links(["Cocoa", "Metal", "QuartzCore"])
```

### Android

**Project Type:**
```python
with project("AndroidApp"):
    sharedlib()  # Native library: libAndroidApp.so
```

**Settings:**
```python
with filter("system:Android"):
    androidapplicationid("com.mycompany.myapp")
    androidminsdk(21)
    androidtargetsdk(33)
    androidversioncode(1)
    androidversionname("1.0.0")
    
    links(["log", "android", "EGL", "GLESv3"])
```

**APK Signing:**
```python
with filter("configurations:Release"):
    androidsign(True)
    androidkeystore("/path/to/release.jks")
    androidkeystorepass("mypassword")
    androidkeyalias("mykey")
```

**Build Output:**
- Native library: `libMyApp.so`
- APK (with Java wrapper): `MyApp.apk`

### iOS

**Requirements:**
- Must build on macOS
- Xcode installed
- iOS SDK installed

**Settings:**
```python
with filter("system:iOS"):
    defines(["TARGET_OS_IPHONE", "TARGET_OS_IOS"])
    systemversion("14.0")  # Minimum iOS version
```

### Emscripten (Web)

**Output Files:**
- `app.html` - HTML wrapper
- `app.js` - JavaScript glue code
- `app.wasm` - WebAssembly binary

**Settings:**
```python
with filter("system:Emscripten"):
    postbuild([
        "python3 scripts/generate_html.py"
    ])
```

**Optimization:**
```python
with filter("configurations:Release"):
    optimize("Full")  # -O3
```

---

## VSCode Integration

### Generate Configuration
```bash
nken gen --ide vscode --platform Linux
```

This creates:
- `.vscode/c_cpp_properties.json` - IntelliSense
- `.vscode/tasks.json` - Build tasks
- `.vscode/launch.json` - Debug configurations

### Use in VSCode
1. Open workspace in VSCode
2. Press `Ctrl+Shift+B` to build
3. Press `F5` to debug

---

## Tips & Best Practices

### 1. Organize by Platform
```
MyProject/
├── src/
│   ├── common/          # Shared code
│   ├── windows/         # Windows-specific
│   ├── linux/           # Linux-specific
│   ├── macos/           # macOS-specific
│   ├── android/         # Android-specific
│   └── ios/             # iOS-specific
```

### 2. Use Filters Wisely
```python
# Good: Platform-specific
with filter("system:Windows"):
    files(["/src/windows/**.cpp"])

# Good: Configuration-specific
with filter("configurations:Debug"):
    defines(["DEBUG_LOGGING"])
```

### 3. Separate Graphics Backends
```python
with filter("system:Windows"):
    files(["/renderer/d3d11/**.cpp"])

with filter("system:Linux"):
    files(["/renderer/vulkan/**.cpp"])

with filter("system:MacOS"):
    files(["/renderer/metal/**.mm"])  # Objective-C++
```

### 4. Asset Management
```python
dependfiles([
    "assets/**",        # All assets
    "config/*.json"     # Config files
])
```

### 5. Testing Multi-Platform
```bash
# Test all platforms (if available)
nken build --platform Windows
nken build --platform Linux
nken build --platform MacOS
nken build --platform Android
```

---

## Troubleshooting

### Compiler Not Found
```
✗ Compiler not found: g++
```
**Solution:** Install compiler or specify full path:
```python
cppcompiler("/usr/bin/g++-12")
```

### Library Not Found
```
ld: cannot find -lkernel32
```
**Solution:** Wrong platform libraries. Use filters:
```python
with filter("system:Windows"):
    links(["kernel32"])

with filter("system:Linux"):
    links(["pthread"])
```

### Android NDK Not Found
```
✗ Android NDK not configured
```
**Solution:** Set environment variable:
```bash
export ANDROID_NDK_ROOT=/path/to/ndk
```

### Emscripten Not Found
```
✗ em++ not found
```
**Solution:** Source EMSDK environment:
```bash
source /path/to/emsdk/emsdk_env.sh
```

---

## Complete Example

See `Examples/multiplatform.nken` for a complete working example with:
- All 6 platforms
- Platform-specific graphics backends
- Asset management
- APK signing
- iOS bundle creation
- WebAssembly output

---

Happy cross-platform building! 🚀
