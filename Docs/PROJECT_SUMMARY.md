# Nken Build System - Project Summary

## What's Included

This ZIP archive contains a complete, functional build system called "Nken" - a modern Python-based alternative to Premake5 with direct compilation capabilities.

## Key Features Implemented

### ✅ Core Build System
- Direct compilation without intermediate makefiles
- Parallel compilation with configurable job count
- Intelligent caching system (SHA256-based)
- Incremental builds
- Cross-platform support (Windows, Linux, MacOS)

### ✅ Configuration System
- Python-based DSL for clean configuration
- Context managers for scoped settings
- Variable expansion with %{variable} syntax
- Cross-project property references
- File pattern matching (*, **, !)

### ✅ Dependency Management
- Automatic dependency resolution
- Topological sorting for build order
- Auto-linking of dependencies
- Circular dependency detection

### ✅ Commands Implemented
- `build` - Build projects with parallel compilation
- `clean` - Remove build artifacts
- `rebuild` - Clean and build
- `run` - Execute built programs
- `info` - Display configuration
- `package` - Placeholder for packaging

### ✅ Advanced Features
- Multiple toolchain support (Clang, GCC, MSVC)
- Configuration-specific settings (Debug, Release, Dist)
- Platform-specific settings
- Filter system for conditional configuration
- Test suite support with automatic main injection
- File exclusion patterns

### ✅ Example Project
Complete working example with:
- Core library (system utilities, timer)
- Logger library (logging system)
- Jenga library (build system core)
- Unitest library (testing framework)
- CLI application (demonstrates all features)

## Project Structure

```
Jenga_Build_System/
├── README.md              # Complete documentation
├── QUICKSTART.md          # Quick start guide
├── ARCHITECTURE.md        # Technical architecture
├── .gitignore            # Git ignore rules
├── nken.bat              # Windows launcher
├── nken.sh               # Unix/Linux/Mac launcher
├── jenga.nken            # Configuration file
│
├── Tools/                # Build system implementation
│   ├── nken.py          # Main entry point
│   ├── core.py          # API exports
│   ├── core/            # Core modules
│   │   ├── api.py       # DSL definitions
│   │   ├── loader.py    # Config loader
│   │   ├── buildsystem.py  # Compilation engine
│   │   ├── variables.py # Variable expansion
│   │   └── commands.py  # Command registry
│   ├── Commands/        # Command implementations
│   │   ├── build.py
│   │   ├── clean.py
│   │   ├── rebuild.py
│   │   ├── run.py
│   │   ├── info.py
│   │   └── package.py
│   └── utils/           # Utilities
│       ├── display.py   # Console output
│       └── reporter.py  # Build reporting
│
├── Core/                # Core library project
│   └── src/Core/
│       ├── Core.h
│       └── Core.cpp
│
├── Logger/              # Logger library project
│   └── src/Logger/
│       ├── Logger.h
│       └── Logger.cpp
│
├── Jenga/               # Jenga library project
│   └── src/Jenga/
│       ├── Jenga.h
│       └── Jenga.cpp
│
├── Unitest/             # Unit test library project
│   └── src/Unitest/
│       ├── Unitest.h
│       └── Unitest.cpp
│
└── CLI/                 # CLI application project
    └── main.cpp
```

## What Works

1. **Configuration Loading**: Reads .nken files and builds workspace/project structure
2. **Variable Expansion**: Full support for %{variable} and %{project.property}
3. **File Pattern Matching**: *.cpp, **.cpp, !exclude.cpp all work
4. **Parallel Compilation**: Compiles multiple files simultaneously
5. **Build Cache**: Skips unchanged files for faster builds
6. **Dependency Resolution**: Builds projects in correct order
7. **Cross-Platform**: Detects platform and adjusts accordingly
8. **Toolchain Support**: Can use different compilers

## How to Test

### Windows
```cmd
cd Jenga_Build_System
nken.bat info
nken.bat build
nken.bat run
```

### Linux/Mac
```bash
cd Jenga_Build_System
chmod +x nken.sh
./nken.sh info
./nken.sh build
./nken.sh run
```

## Expected Output

When you run `nken build`, you should see:
1. Banner with Nken logo
2. Configuration loading message
3. Build progress for each project
4. Parallel compilation output
5. Linking messages
6. Build statistics
7. Success message

When you run `nken run`, the CLI app will:
1. Initialize all systems
2. Display platform info
3. Create a test project
4. Run unit tests
5. Show execution time
6. Exit with test result code

## Configuration Example

The included `jenga.nken` demonstrates:

```python
with workspace("Jenga"):
    configurations(["Debug", "Release", "Dist"])
    platforms(["Windows", "Linux", "MacOS"])
    startproject("CLI")
    
    with toolchain("default", "clang++"):
        defines(["NKEN_TOOLCHAIN_CLANG"])
    
    with project("Core"):
        staticlib()
        language("C++")
        cppdialect("C++20")
        
        files(["Core/src/**.cpp"])
        includedirs(["Core/src"])
        
        objdir("Build/Obj/%{cfg.buildcfg}/%{prj.name}")
        targetdir("Build/Lib/%{cfg.buildcfg}")
        
        with filter("configurations:Debug"):
            defines(["DEBUG"])
            optimize("Off")
            symbols("On")
```

## Known Limitations

1. **Compiler Detection**: Currently requires compiler in PATH or manual specification
2. **Android/iOS**: Support planned but not yet implemented
3. **Precompiled Headers**: Not yet supported
4. **IDE Integration**: No project file generation yet
5. **Package Command**: Placeholder only

## Future Enhancements

- Complete Android/iOS/Emscripten support
- Precompiled header support
- IDE project generation (VSCode, Visual Studio)
- Remote/distributed compilation
- Package management integration
- Binary package generation
- More sophisticated caching

## Requirements

- Python 3.7 or higher
- C++ compiler (clang++, g++, or cl.exe)
- Platform-specific:
  - Windows: MSVC, MinGW, or Clang
  - Linux: GCC or Clang (sudo apt install build-essential)
  - MacOS: Xcode Command Line Tools

## Notes

1. This is a functional demonstration/prototype
2. All core features are implemented and working
3. Code is well-structured and documented
4. Easy to extend with new features
5. Configuration syntax is clean and intuitive

## Support

For issues or questions, refer to:
- README.md for usage documentation
- ARCHITECTURE.md for technical details
- Source code comments for implementation details

## License

MIT License - Free to use and modify

## Credits

Created as a demonstration of:
- Python-based build systems
- Direct compilation
- Parallel processing
- Intelligent caching
- Cross-platform development

Enjoy building with Nken! 🚀
