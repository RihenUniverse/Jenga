# Nken Build System - Release Notes

## 🎉 Version 1.0 - Production Ready

### ✨ Major Features

#### 1. **Automatic Platform Detection**
- Automatically detects Windows, Linux, or MacOS
- No need to specify `--platform` unless cross-compiling
- Example: `nken build` automatically uses current platform

#### 2. **Intelligent Library Linking**
- **Automatic filtering** of system libraries by platform
- **Full path resolution** for internal dependencies
- **No manual path configuration** needed

```python
with filter("system:Linux"):
    links(["pthread", "dl", "m"])  # Only linked on Linux

with filter("system:Windows"):
    links(["kernel32", "user32"])  # Only linked on Windows
```

#### 3. **File Dependencies (NEW)**
Copy files/folders automatically after build:

```python
with project("GameEngine"):
    consoleapp()
    
    # Copy assets, configs, DLLs automatically
    dependfiles([
        "assets/**",           # All files in assets/
        "config/*.json",       # All JSON configs
        "libs/*.dll",          # External DLLs
        "data/levels/**"       # Game levels
    ])
```

**Use Cases:**
- Asset management (images, sounds, data)
- Configuration files
- External DLLs/SOs
- Documentation

#### 4. **Embedded Resources (NEW)**
Compile resources directly into executable:

```python
with project("WindowsApp"):
    windowedapp()
    
    # Embed resources in executable
    embedresources([
        "app.ico",           # Application icon
        "manifest.xml",      # Windows manifest
        "resources.rc"       # Resource script
    ])
```

#### 5. **Automatic DLL/SO Copying**
When building an executable that depends on shared libraries:
- **Automatically copies** `.dll` (Windows), `.so` (Linux), `.dylib` (MacOS)
- Copies to executable's directory
- **No manual intervention** needed

```python
# Engine is a shared library
with project("Engine"):
    sharedlib()
    # ...

# Game depends on Engine
with project("Game"):
    consoleapp()
    dependson(["Engine"])  # Engine.dll automatically copied!
```

#### 6. **Android APK Signing (NEW)**
Sign your Android APKs for release:

```python
with project("AndroidApp"):
    sharedlib()  # Native library
    
    androidsign(True)
    androidkeystore("/path/to/keystore.jks")
    androidkeystorepass("your_password")
    androidkeyalias("release_key")
    
    androidapplicationid("com.mycompany.app")
    androidminsdk(21)
    androidtargetsdk(33)
```

### 🔧 API Changes

#### Simplified Names
| Old Name | New Name |
|----------|----------|
| `toolchain_select()` | `usetoolchain()` |
| `prebuildcommands()` | `prebuild()` |
| `postbuildcommands()` | `postbuild()` |
| `prelinkcommands()` | `prelink()` |
| `postlinkcommands()` | `postlink()` |

#### New Functions
- `dependfiles()` - Copy files after build
- `embedresources()` - Embed resources in executable
- `androidsign()` - Enable APK signing
- `androidkeystore()` - Set keystore path
- `androidkeystorepass()` - Set keystore password
- `androidkeyalias()` - Set key alias

### 📝 Configuration Example

```python
# No import needed - API auto-injected!

with workspace("MyGame"):
    configurations(["Debug", "Release", "Dist"])
    platforms(["Windows", "Linux", "MacOS", "Android"])
    
    # Toolchain with explicit paths
    with toolchain("default", "g++"):
        defines(["MY_TOOLCHAIN"])
        cppcompiler("/usr/bin/g++-12")
        ccompiler("/usr/bin/gcc-12")
    
    # Shared library (engine)
    with project("Engine"):
        sharedlib()
        language("C++")
        cppdialect("C++20")
        
        usetoolchain("default")
        
        files(["%{wks.location}/Engine/src/**.cpp"])
        includedirs(["%{wks.location}/Engine/include"])
        
        objdir("%{wks.location}/Build/Obj/%{cfg.buildcfg}/%{prj.name}")
        targetdir("%{wks.location}/Build/Lib/%{cfg.buildcfg}")
    
    # Game executable
    with project("Game"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        
        usetoolchain("default")
        
        files(["%{wks.location}/Game/src/**.cpp"])
        
        # Cross-project references
        includedirs([
            "%{wks.location}/Game/include",
            "%{Engine.location}/Engine/include"
        ])
        
        dependson(["Engine"])  # Auto-links + copies DLL
        
        # Copy game assets
        dependfiles([
            "assets/**",
            "config/*.json"
        ])
        
        # Build hooks
        prebuild([
            "echo Starting Game build..."
        ])
        
        postbuild([
            "echo Game built successfully!"
        ])
        
        objdir("%{wks.location}/Build/Obj/%{cfg.buildcfg}/%{prj.name}")
        targetdir("%{wks.location}/Build/Bin/%{cfg.buildcfg}")
        
        # Platform-specific
        with filter("system:Windows"):
            defines(["PLATFORM_WINDOWS"])
            links(["user32", "gdi32"])  # Only on Windows
        
        with filter("system:Linux"):
            defines(["PLATFORM_LINUX"])
            links(["pthread", "dl", "m"])  # Only on Linux
```

### 🚀 Usage

#### Build Commands
```bash
# Auto-detect platform
nken build

# Specify platform for cross-compilation
nken build --platform Windows
nken build --platform Android

# Specify configuration
nken build --config Release

# Build specific project
nken build --project Engine

# Parallel build with 8 jobs
nken build --jobs 8

# Verbose output
nken build --verbose
```

#### Other Commands
```bash
nken clean              # Clean build artifacts
nken rebuild            # Clean + build
nken run                # Run executable
nken run --config Release
nken info               # Show workspace info
```

### 🐛 Fixed Issues

1. ✅ **Platform Detection** - Automatically detects current OS
2. ✅ **Library Linking** - Uses full paths for internal libs
3. ✅ **System Libraries** - Filters by platform automatically
4. ✅ **DLL Copying** - Automatic for shared lib dependencies
5. ✅ **File Patterns** - `**.cpp` now works correctly
6. ✅ **Header Files** - No longer compiled (filtered out)
7. ✅ **Cross-References** - `%{Project.location}` works perfectly

### 📦 What's Included

- **Core System** - Build engine with parallel compilation
- **Build Cache** - SHA256-based incremental builds
- **Toolchain Management** - Multiple compiler support
- **Platform Support** - Windows, Linux, MacOS, Android, Emscripten
- **Documentation** - Comprehensive guides and examples
- **Example Project** - Working demo with 5 projects

### 🎯 Key Improvements

1. **Zero Configuration** - Works out of the box
2. **Intelligent Defaults** - Sensible defaults for everything
3. **Platform Aware** - Automatic platform handling
4. **User Friendly** - Clear error messages
5. **Production Ready** - Tested and working

### 📚 Documentation

- `README.md` - Main documentation
- `QUICKSTART.md` - Get started in 5 minutes
- `ANDROID_EMSCRIPTEN_GUIDE.md` - Mobile/Web development
- `ARCHITECTURE.md` - Technical details
- `WHATS_NEW.md` - Feature overview

### 🧪 Testing

All core features tested and working:

- ✅ `nken info` - Shows workspace configuration
- ✅ `nken build` - Compiles all projects
- ✅ `nken clean` - Cleans artifacts
- ✅ `nken rebuild` - Clean + build
- ✅ `nken run` - Executes with correct output
- ✅ Cross-project references work
- ✅ Platform detection works
- ✅ Library linking works
- ✅ Parallel compilation works
- ✅ Build cache works

### 🎓 Migration Guide

If upgrading from previous version:

1. **Remove imports** from `.nken` files:
   ```python
   # Remove this line:
   # from Tools.core import *
   ```

2. **Update function names**:
   ```python
   # Old:
   toolchain_select("gcc")
   prebuildcommands([...])
   
   # New:
   usetoolchain("gcc")
   prebuild([...])
   ```

3. **Add platform-specific filters**:
   ```python
   with filter("system:Linux"):
       links(["pthread", "dl", "m"])
   ```

4. **Use new features**:
   ```python
   # Copy assets automatically
   dependfiles(["assets/**"])
   
   # Embed resources
   embedresources(["icon.ico"])
   ```

### 💡 Pro Tips

1. **No need to specify platform** - It's auto-detected!
2. **Use cross-project references** - `%{Project.location}`
3. **Use dependfiles** for assets - No manual copying
4. **Platform-specific in filters** - Keep code clean
5. **Use verbose mode** for debugging - `--verbose`

### 🚧 Future Enhancements

- [ ] IDE project generation (Visual Studio, Xcode)
- [ ] Precompiled headers support
- [ ] Remote/distributed compilation
- [ ] Full Android APK packaging
- [ ] iOS support completion
- [ ] Package management integration

---

## 🎉 Thank You!

Nken Build System is now production-ready and fully functional!

**Happy Building!** 🚀
