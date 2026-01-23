# Nken Build System - Android & Emscripten Guide

## Android Build Support

### Prerequisites

1. **Android SDK**: Download from https://developer.android.com/studio
2. **Android NDK**: Install via Android Studio SDK Manager or standalone
3. **Java JDK**: Required for APK building

### Configuration

In your `.nken` file:

```python
from Tools.core import *

with workspace("MyAndroidApp"):
    configurations(["Debug", "Release"])
    platforms(["Android"])  # Add Android platform
    
    # Configure Android SDK/NDK paths
    androidsdkpath("C:/Users/YourName/AppData/Local/Android/Sdk")
    androidndkpath("C:/Users/YourName/AppData/Local/Android/Sdk/ndk/25.2.9519653")
    javajdkpath("C:/Program Files/Java/jdk-17")
    
    # Configure Android toolchain
    with toolchain("android", "aarch64-linux-android21-clang++"):
        # The toolchain will be auto-configured from NDK path
        defines(["ANDROID", "__ANDROID__"])
    
    with project("MyNativeLib"):
        sharedlib()  # Android native libraries are .so files
        language("C++")
        cppdialect("C++17")
        
        # Select Android toolchain
        toolchain_select("android")
        
        files([
            "%{wks.location}/src/**.cpp"
        ])
        
        includedirs([
            "%{wks.location}/src"
        ])
        
        # Android-specific settings
        androidapplicationid("com.mycompany.myapp")
        androidminsdk(21)  # API 21 = Android 5.0
        androidtargetsdk(33)  # API 33 = Android 13
        androidversioncode(1)
        androidversionname("1.0.0")
        
        objdir("%{wks.location}/Build/Android/Obj/%{cfg.buildcfg}")
        targetdir("%{wks.location}/Build/Android/Lib/%{cfg.buildcfg}")
```

### Building for Android

```bash
# Build for Android
./nken.sh build --platform Android --toolchain android

# Output: libMyNativeLib.so in Build/Android/Lib/
```

### NDK Toolchain Details

The Android NDK provides:
- **Compiler**: `clang++` (LLVM-based)
- **Target Architectures**:
  - ARM64: `aarch64-linux-android` (64-bit, recommended)
  - ARM: `armv7a-linux-androideabi` (32-bit)
  - x86_64: `x86_64-linux-android` (64-bit)
  - x86: `i686-linux-android` (32-bit)

### Architecture-Specific Builds

```python
# In your .nken file

with project("MyNativeLib"):
    # ... other settings ...
    
    with filter("architecture:ARM64"):
        defines(["ARM64"])
        # Toolchain automatically uses aarch64-linux-android
    
    with filter("architecture:ARM"):
        defines(["ARM32"])
        # Toolchain automatically uses armv7a-linux-androideabi
```

Build command:
```bash
./nken.sh build --platform Android --architecture ARM64
```

### Advanced: APK Creation

While Nken focuses on native library compilation, you can use postbuild commands to create APKs:

```python
with project("MyAndroidApp"):
    # ... configure native library ...
    
    postbuildcommands([
        # Copy library to Android project
        "mkdir -p android/app/src/main/jniLibs/arm64-v8a",
        "cp %{prj.targetdir}/libMyNativeLib.so android/app/src/main/jniLibs/arm64-v8a/",
        
        # Build APK with Gradle
        "cd android && ./gradlew assembleDebug"
    ])
```

---

## Emscripten Build Support

### Prerequisites

1. **Emscripten SDK**: https://emscripten.org/docs/getting_started/downloads.html

```bash
# Install Emscripten
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh  # Linux/Mac
# or
emsdk_env.bat  # Windows
```

2. Verify installation:
```bash
emcc --version
em++ --version
```

### Configuration

In your `.nken` file:

```python
from Tools.core import *

with workspace("MyWebApp"):
    configurations(["Debug", "Release"])
    platforms(["Emscripten"])  # Add Emscripten platform
    
    # Configure Emscripten toolchain
    with toolchain("emscripten", "em++"):
        defines(["EMSCRIPTEN", "__EMSCRIPTEN__", "WEB_BUILD"])
        
        # Emscripten-specific flags
        cxxflags([
            "-s", "WASM=1",
            "-s", "USE_SDL=2",  # If using SDL
        ])
        
        ldflags([
            "-s", "WASM=1",
            "-s", "ALLOW_MEMORY_GROWTH=1",
            "-s", "EXPORTED_FUNCTIONS=['_main']",
            "-s", "EXPORTED_RUNTIME_METHODS=['ccall','cwrap']",
        ])
    
    with project("MyWebApp"):
        windowedapp()  # Or consoleapp
        language("C++")
        cppdialect("C++17")
        
        # Select Emscripten toolchain
        toolchain_select("emscripten")
        
        files([
            "%{wks.location}/src/**.cpp"
        ])
        
        includedirs([
            "%{wks.location}/src"
        ])
        
        # Platform-specific settings
        with filter("system:Emscripten"):
            defines(["USE_WEBGL"])
            
            # Output .html and .wasm files
            targetname("webapp")
            
            # Additional Emscripten settings
            postbuildcommands([
                # Generate custom HTML shell
                "echo Generating web files...",
                # Copy assets to web directory
                "cp -r assets %{prj.targetdir}/"
            ])
        
        objdir("%{wks.location}/Build/Web/Obj/%{cfg.buildcfg}")
        targetdir("%{wks.location}/Build/Web/%{cfg.buildcfg}")
```

### Building for Web

```bash
# Build for Emscripten
./nken.sh build --platform Emscripten --toolchain emscripten

# Output: webapp.html, webapp.js, webapp.wasm in Build/Web/
```

### Testing Your Web App

```bash
# Start a local web server
cd Build/Web/Debug
python3 -m http.server 8000

# Open browser to http://localhost:8000/webapp.html
```

### Optimization Levels

```python
with project("MyWebApp"):
    # ... other settings ...
    
    with filter("configurations:Debug"):
        defines(["DEBUG"])
        optimize("Off")  # -O0 -g
    
    with filter("configurations:Release"):
        defines(["NDEBUG"])
        optimize("Speed")  # -O2
    
    with filter("configurations:Dist"):
        defines(["NDEBUG", "DIST"])
        optimize("Full")  # -O3 -flto (Link Time Optimization)
```

### Advanced Emscripten Features

#### Threading Support

```python
with toolchain("emscripten", "em++"):
    defines(["USE_PTHREADS"])
    
    cxxflags([
        "-s", "USE_PTHREADS=1",
        "-pthread"
    ])
    
    ldflags([
        "-s", "USE_PTHREADS=1",
        "-s", "PTHREAD_POOL_SIZE=4"
    ])
```

#### Memory Configuration

```python
with toolchain("emscripten", "em++"):
    ldflags([
        "-s", "INITIAL_MEMORY=33554432",  # 32MB
        "-s", "MAXIMUM_MEMORY=67108864",  # 64MB
        "-s", "ALLOW_MEMORY_GROWTH=1",
    ])
```

#### File System Support

```python
with toolchain("emscripten", "em++"):
    ldflags([
        "--preload-file", "assets",  # Embed assets folder
        "-s", "FORCE_FILESYSTEM=1",
    ])
```

---

## Complete Multi-Platform Example

```python
from Tools.core import *

with workspace("MultiPlatformApp"):
    configurations(["Debug", "Release"])
    platforms(["Windows", "Linux", "MacOS", "Android", "Emscripten"])
    
    # Toolchains
    with toolchain("default", "clang++"):
        defines(["NATIVE_BUILD"])
    
    with toolchain("android", "aarch64-linux-android21-clang++"):
        defines(["ANDROID"])
    
    with toolchain("emscripten", "em++"):
        defines(["EMSCRIPTEN"])
        cxxflags(["-s", "WASM=1"])
    
    # Android configuration
    androidsdkpath("/path/to/android/sdk")
    androidndkpath("/path/to/android/ndk")
    
    with project("MyApp"):
        consoleapp()
        language("C++")
        cppdialect("C++17")
        
        files(["%{wks.location}/src/**.cpp"])
        includedirs(["%{wks.location}/src"])
        
        objdir("%{wks.location}/Build/Obj/%{cfg.system}/%{cfg.buildcfg}")
        targetdir("%{wks.location}/Build/Bin/%{cfg.system}/%{cfg.buildcfg}")
        
        # Native platforms
        with filter("system:Windows"):
            toolchain_select("default")
            defines(["PLATFORM_WINDOWS"])
        
        with filter("system:Linux"):
            toolchain_select("default")
            defines(["PLATFORM_LINUX"])
        
        with filter("system:MacOS"):
            toolchain_select("default")
            defines(["PLATFORM_MACOS"])
        
        # Android
        with filter("system:Android"):
            toolchain_select("android")
            defines(["PLATFORM_ANDROID"])
            sharedlib()  # Override to shared lib for Android
        
        # Emscripten
        with filter("system:Emscripten"):
            toolchain_select("emscripten")
            defines(["PLATFORM_WEB"])
            targetname("webapp")
```

Build commands:
```bash
# Native
./nken.sh build --platform Windows
./nken.sh build --platform Linux
./nken.sh build --platform MacOS

# Android
./nken.sh build --platform Android --toolchain android

# Web
./nken.sh build --platform Emscripten --toolchain emscripten
```

---

## Troubleshooting

### Android

**Issue**: NDK not found
- Verify `androidndkpath` is correct
- Check NDK is installed via Android Studio SDK Manager

**Issue**: Compiler not found
- Ensure NDK version is compatible (25.x recommended)
- Check host toolchain matches your OS

### Emscripten

**Issue**: emcc not found
- Run `source ./emsdk_env.sh` (or `.bat` on Windows)
- Verify `EMSDK` environment variable is set

**Issue**: Module not loading in browser
- Check browser console for errors
- Ensure you're using a local server (not file://)
- Verify CORS settings if loading external files

---

## Summary

Nken provides first-class support for cross-platform builds:

✅ **Native**: Windows, Linux, MacOS with standard toolchains
✅ **Android**: Full NDK integration for native libraries
✅ **Web**: Emscripten/WebAssembly support with optimization
✅ **Cross-references**: Use `%{Project.location}` across platforms
✅ **Build hooks**: Pre/post build commands for custom workflows
✅ **Toolchain selection**: Choose compiler per project or platform

Happy cross-platform building! 🚀
