# Nken Build System - What's New (Updated Version)

## 🎉 New Features & Improvements

### 1. ✨ Enhanced Variable Expansion

#### Cross-Project Location References
Now you can reference other projects' locations directly!

```python
with project("MyApp"):
    # Reference dependency project locations
    includedirs([
        "%{wks.location}/MyApp/src",
        "%{Core.location}/Core/include",      # ← NEW!
        "%{Logger.location}/Logger/include",   # ← NEW!
        "%{Engine.location}/Engine/include"    # ← NEW!
    ])
    
    dependson(["Core", "Logger", "Engine"])
```

**Benefits:**
- No need to hardcode paths
- Automatically resolves to correct location
- Works even if projects are in different directories
- Only accessible if project is in `dependson()`

#### Workspace Location Variables
Use `%{wks.location}` for workspace-relative paths:

```python
files([
    "%{wks.location}/src/**.cpp",  # Always relative to workspace
    "%{wks.location}/include/**.h"
])
```

### 2. 🔧 Per-Project Toolchain Selection

You can now specify which toolchain each project should use:

```python
with workspace("MultiCompiler"):
    # Define multiple toolchains
    with toolchain("clang", "clang++"):
        defines(["USE_CLANG"])
    
    with toolchain("gcc", "g++"):
        defines(["USE_GCC"])
    
    with toolchain("msvc", "cl"):
        defines(["USE_MSVC"])
    
    # Project 1 uses Clang
    with project("FastLib"):
        staticlib()
        toolchain_select("clang")  # ← NEW!
        # ...
    
    # Project 2 uses GCC
    with project("CompatLib"):
        staticlib()
        toolchain_select("gcc")    # ← NEW!
        # ...
    
    # Project 3 uses MSVC
    with project("WinApp"):
        windowedapp()
        toolchain_select("msvc")   # ← NEW!
        # ...
```

### 3. 📂 Explicit Compiler Paths

Specify exact paths to compilers in toolchain definitions:

```python
with toolchain("custom-gcc", "g++"):
    cppcompiler("/usr/local/gcc-12/bin/g++")      # ← NEW!
    ccompiler("/usr/local/gcc-12/bin/gcc")        # ← NEW!
    toolchaindir("/usr/local/gcc-12/bin")         # ← NEW!
```

**Use Cases:**
- Multiple compiler versions installed
- Custom compiler installations
- Cross-compilation toolchains
- Android NDK, Emscripten, etc.

### 4. 🎯 Build Hooks

Add custom commands at different stages of the build:

```python
with project("MyApp"):
    # Before compilation starts
    prebuildcommands([
        "echo Starting build...",
        "python scripts/generate_version.py"
    ])
    
    # After compilation, before linking
    prelinkcommands([
        "echo Preparing to link...",
        "python scripts/check_symbols.py"
    ])
    
    # After linking
    postlinkcommands([
        "echo Signing binary...",
        "codesign -s MyIdentity %{prj.targetdir}/%{prj.name}"
    ])
    
    # After entire build complete
    postbuildcommands([
        "echo Copying assets...",
        "cp -r assets %{prj.targetdir}/",
        "echo Build complete!"
    ])
```

**Common Uses:**
- Copy assets/resources
- Code signing
- Version file generation
- Documentation generation
- Package creation
- Deployment scripts

### 5. 📱 Android NDK Support

Full Android native library compilation:

```python
with workspace("AndroidApp"):
    platforms(["Android"])
    
    # Configure Android SDK/NDK
    androidsdkpath("/path/to/android/sdk")
    androidndkpath("/path/to/android/ndk")
    
    # Android toolchain (auto-configured)
    with toolchain("android", "aarch64-linux-android21-clang++"):
        defines(["ANDROID"])
    
    with project("NativeLib"):
        sharedlib()  # .so for Android
        toolchain_select("android")
        
        androidapplicationid("com.mycompany.myapp")
        androidminsdk(21)
        androidtargetsdk(33)
        
        # ...
```

**Build Command:**
```bash
nken build --platform Android --toolchain android
```

### 6. 🌐 Emscripten/WebAssembly Support

Compile to WebAssembly with Emscripten:

```python
with workspace("WebApp"):
    platforms(["Emscripten"])
    
    with toolchain("emscripten", "em++"):
        defines(["EMSCRIPTEN"])
        cxxflags(["-s", "WASM=1"])
        ldflags(["-s", "ALLOW_MEMORY_GROWTH=1"])
    
    with project("WebGame"):
        windowedapp()
        toolchain_select("emscripten")
        
        with filter("system:Emscripten"):
            targetname("game")  # → game.html, game.js, game.wasm
```

**Build Command:**
```bash
nken build --platform Emscripten --toolchain emscripten
```

### 7. 🔄 Fixed Import Issues

All relative import problems resolved:
- Works when run from any directory
- Consistent module loading
- No more import errors

### 8. 🏗️ Mandatory Project Location

Projects now properly inherit workspace location:

```python
with workspace("MyWorkspace"):
    # Location set automatically to .nken file directory
    
    with project("MyProject"):
        # Project location automatically set to workspace location
        # Can be overridden with: location("custom/path")
```

### 9. 📋 Enhanced Configuration Examples

New comprehensive examples included:

- **jenga.nken**: Basic multi-library project
- **Examples/advanced.nken**: Full cross-platform example with:
  - Multiple toolchains
  - Android and Emscripten support
  - Build hooks
  - Cross-project references
  - Platform-specific settings

---

## 📖 Updated API Reference

### New Functions

```python
# Build Hooks
prebuildcommands(["command1", "command2"])
postbuildcommands(["command1", "command2"])
prelinkcommands(["command1", "command2"])
postlinkcommands(["command1", "command2"])

# Toolchain Selection
toolchain_select("toolchain_name")

# Toolchain Configuration
toolchaindir("/path/to/toolchain/bin")
```

### Enhanced Functions

```python
# Now supports full paths
cppcompiler("/usr/local/bin/clang++")
ccompiler("/usr/local/bin/clang")
```

### New Variables

```python
"%{wks.location}"           # Workspace directory
"%{ProjectName.location}"   # Other project's location
"%{ProjectName.targetdir}"  # Other project's output dir
"%{ProjectName.name}"       # Other project's name
# ... and more project properties
```

---

## 🎓 Usage Examples

### Example 1: Multi-Compiler Project

```python
with workspace("MultiCompiler"):
    with toolchain("clang", "clang++"):
        defines(["USE_CLANG"])
    
    with toolchain("gcc", "g++"):
        defines(["USE_GCC"])
    
    # Use Clang for performance-critical code
    with project("FastMath"):
        staticlib()
        toolchain_select("clang")
        files(["FastMath/**.cpp"])
    
    # Use GCC for compatibility
    with project("PortableLib"):
        staticlib()
        toolchain_select("gcc")
        files(["PortableLib/**.cpp"])
```

Build specific toolchain:
```bash
nken build --project FastMath   # Uses Clang
nken build --project PortableLib # Uses GCC
```

### Example 2: Asset Copying with Build Hooks

```python
with project("GameEngine"):
    windowedapp()
    
    files(["Engine/**.cpp"])
    
    postbuildcommands([
        # Copy game assets
        "mkdir -p %{prj.targetdir}/assets",
        "cp -r Assets/* %{prj.targetdir}/assets/",
        
        # Copy DLLs (Windows)
        "cp ThirdParty/SDL2.dll %{prj.targetdir}/",
        
        # Generate manifest
        "python scripts/generate_manifest.py %{prj.targetdir}"
    ])
```

### Example 3: Cross-Project References

```python
with workspace("ComplexApp"):
    with project("Core"):
        staticlib()
        files(["%{wks.location}/Core/**.cpp"])
        includedirs(["%{wks.location}/Core/include"])
    
    with project("Network"):
        staticlib()
        files(["%{wks.location}/Network/**.cpp"])
        
        # Reference Core's include directory
        includedirs([
            "%{wks.location}/Network/include",
            "%{Core.location}/Core/include"  # ← Cross-reference!
        ])
        
        dependson(["Core"])
    
    with project("GameClient"):
        windowedapp()
        files(["%{wks.location}/Client/**.cpp"])
        
        # Reference all dependencies
        includedirs([
            "%{wks.location}/Client/include",
            "%{Core.location}/Core/include",
            "%{Network.location}/Network/include"
        ])
        
        dependson(["Core", "Network"])
```

---

## 🚀 Migration Guide

If you have an existing .nken file:

### 1. Update Variable References

**Before:**
```python
files(["Core/src/**.cpp"])
includedirs(["Core/include"])
```

**After (Recommended):**
```python
files(["%{wks.location}/Core/src/**.cpp"])
includedirs(["%{wks.location}/Core/include"])
```

### 2. Use Cross-Project References

**Before:**
```python
with project("App"):
    includedirs([
        "App/include",
        "Core/include",      # Hardcoded path
        "Logger/include"     # Hardcoded path
    ])
    dependson(["Core", "Logger"])
```

**After:**
```python
with project("App"):
    includedirs([
        "%{wks.location}/App/include",
        "%{Core.location}/Core/include",      # Dynamic!
        "%{Logger.location}/Logger/include"   # Dynamic!
    ])
    dependson(["Core", "Logger"])
```

### 3. Add Build Hooks (Optional)

```python
with project("MyApp"):
    # ... existing config ...
    
    postbuildcommands([
        "echo Build complete for %{prj.name}!",
        "cp -r assets %{prj.targetdir}/"
    ])
```

### 4. Specify Toolchain (Optional)

```python
with project("MyLib"):
    staticlib()
    
    # Use specific toolchain
    toolchain_select("clang")
    
    # ... rest of config ...
```

---

## 📝 Complete Working Example

See `Examples/advanced.nken` for a fully-featured example demonstrating:

✅ Multiple toolchains (Clang, GCC, MSVC, Android, Emscripten)
✅ Cross-project location references
✅ Build hooks (pre/post build, pre/post link)
✅ Platform-specific settings (Windows, Linux, Mac, Android, Web)
✅ Asset management
✅ Multiple configurations (Debug, Release, Dist)

---

## 🐛 Bug Fixes

- ✅ Fixed import errors when running from different directories
- ✅ Fixed relative import issues in loader.py and buildsystem.py
- ✅ Proper toolchain selection per project
- ✅ Project location now properly inherits from workspace

---

## 📚 New Documentation

- **ANDROID_EMSCRIPTEN_GUIDE.md**: Complete guide for mobile and web builds
- **Examples/advanced.nken**: Advanced configuration example
- Updated **README.md** with new features
- Updated **ARCHITECTURE.md** with new components

---

## 🎯 What You Can Do Now

1. **Build for multiple platforms** from one configuration
2. **Use different compilers** for different projects
3. **Reference project locations** dynamically
4. **Add custom build steps** with hooks
5. **Compile for Android** natively
6. **Compile for Web** with Emscripten
7. **Specify compiler paths** explicitly

---

## 🚀 Getting Started

```bash
# Extract archive
unzip Nken_Build_System_Complete.zip
cd Jenga_Build_System

# Try the basic example
./nken.sh info
./nken.sh build
./nken.sh run

# Try advanced example
cp Examples/advanced.nken ./
./nken.sh info
```

---

## 💡 Tips

1. **Always use `%{wks.location}`** for workspace-relative paths
2. **Use cross-project references** when you have dependencies
3. **Specify toolchain paths** if you have multiple compiler versions
4. **Use build hooks** for asset copying and deployment
5. **Test each platform separately** during development

Happy building! 🎉
