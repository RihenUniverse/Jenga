# Nken Build System - Technical Architecture

## Architecture Overview

Nken is a Python-based build system that provides direct compilation without intermediate build file generation. It uses a modular architecture with clear separation of concerns.

## Core Components

### 1. Configuration Layer (`core/api.py`)

Defines the DSL (Domain Specific Language) for build configuration:

- **Context Managers**: `workspace`, `project`, `toolchain`, `filter`, `test`
- **Configuration Functions**: Define build settings declaratively
- **Data Classes**: `Workspace`, `Project`, `Toolchain`, `ProjectKind`, etc.

Key Features:
- Python-based configuration (no custom parser needed)
- Context managers for scoped configuration
- Filter system for conditional settings
- Type-safe configuration via dataclasses

### 2. Variable Expansion (`core/variables.py`)

Handles dynamic variable substitution in configuration:

- **Syntax**: `%{variable}` or `%{object.property}`
- **Built-in Variables**: `cfg.buildcfg`, `prj.name`, `wks.location`, etc.
- **Cross-Project References**: `%{ProjectName.property}`
- **File Pattern Expansion**: `*.cpp`, `**.cpp`, `!exclude.cpp`

Implementation:
- Regex-based pattern matching
- Recursive expansion for nested variables
- Path globbing with inclusion/exclusion support

### 3. Configuration Loader (`core/loader.py`)

Loads and executes .nken configuration files:

- Discovers .nken files in directory hierarchy
- Executes Python code with API functions in scope
- Manages global state and workspace context
- Handles errors gracefully

### 4. Build System (`core/buildsystem.py`)

Core compilation and linking engine:

**Features**:
- Parallel compilation using ThreadPoolExecutor
- Incremental builds with SHA256-based caching
- Dependency resolution and build ordering
- Cross-compilation support
- Compiler abstraction

**Components**:
- `Compiler`: Main build orchestrator
- `CompilationUnit`: Represents a single file to compile
- `BuildCache`: Manages compilation cache

**Build Process**:
1. Resolve dependencies (topological sort)
2. Expand file patterns and variables
3. Create compilation units
4. Check cache for each unit
5. Compile units in parallel
6. Link final output

**Caching Strategy**:
- Hash source files (content + mtime)
- Track compiler flags and defines
- Track include directories
- Invalidate on any change

### 5. Command System (`core/commands.py`)

Dynamic command registry:

- Auto-discovers commands from `Commands/` directory
- Each command is a Python module with `execute()` function
- Commands receive parsed options as dictionary

**Available Commands**:
- `build` - Compile projects
- `clean` - Remove artifacts
- `rebuild` - Clean + Build
- `run` - Execute built program
- `info` - Display configuration
- `package` - Package distribution (future)

### 6. Display & Reporting (`utils/`)

User interface layer:

- **display.py**: Colored console output, ANSI codes
- **reporter.py**: Build progress, timing, statistics

## Data Flow

```
.nken File → Loader → API (Workspace/Projects)
                ↓
          Variable Expander
                ↓
           Build System
                ↓
       Compilation Units → Cache Check
                ↓
        Parallel Compiler → Object Files
                ↓
            Linker → Output Binary
```

## Dependency Resolution

Uses topological sorting (Kahn's algorithm):

1. Build dependency graph from `dependson()` declarations
2. Calculate in-degrees for each project
3. Process projects with zero in-degree
4. Remove processed projects and update in-degrees
5. Detect cycles if graph cannot be fully processed

## Parallel Compilation

Uses Python's `concurrent.futures.ThreadPoolExecutor`:

- One thread per compilation unit (up to max jobs)
- Futures track compilation status
- Fail-fast: Cancel all on first error
- Thread-safe progress reporting

## Caching Strategy

Two-level cache:

**Level 1: File Hash**
- SHA256 of file content
- Modification time as fast check
- Stored in `.nken_cache/build_cache.json`

**Level 2: Compilation Context**
- Defines, flags, include dirs
- Invalidated if any change
- Per-source-file granularity

Cache hit = Same hash + Same context = Skip compilation

## Cross-Platform Support

Platform detection and handling:

```python
if platform == "Windows":
    # .exe, .lib, .dll
    # MSVC or MinGW
elif platform == "Linux":
    # no ext, .a, .so
    # GCC or Clang
elif platform == "MacOS":
    # no ext, .a, .dylib
    # Clang (Xcode)
```

Toolchain abstraction allows custom compilers per platform.

## Extensibility Points

### 1. Adding New Commands

Create `Commands/newcommand.py`:

```python
def execute(options: dict) -> bool:
    # Implementation
    return True
```

Automatically discovered and registered.

### 2. Custom Toolchains

```python
with toolchain("custom", "my-compiler"):
    cppcompiler("/path/to/compiler")
    defines(["CUSTOM_TOOLCHAIN"])
    cflags(["-custom-flag"])
```

### 3. Custom Build Steps

Extend `Compiler` class or add pre/post build hooks.

### 4. Platform Support

Add platform-specific logic in:
- `buildsystem.py`: Output extensions, compiler flags
- API: Platform-specific settings

## File Structure

```
Tools/
├── nken.py              # Entry point
├── core.py              # API exports for .nken files
├── core/
│   ├── api.py           # DSL definitions
│   ├── loader.py        # Configuration loader
│   ├── buildsystem.py   # Compilation engine
│   ├── variables.py     # Variable expansion
│   └── commands.py      # Command registry
├── Commands/
│   ├── build.py         # Build command
│   ├── clean.py         # Clean command
│   ├── run.py           # Run command
│   └── ...
└── utils/
    ├── display.py       # Console output
    └── reporter.py      # Build reporting
```

## Performance Optimizations

1. **Parallel Compilation**: N jobs = N CPU cores
2. **Incremental Builds**: Only recompile changed files
3. **Fast Cache Lookup**: mtime check before hash
4. **Lazy Loading**: Import modules on demand
5. **Efficient Path Operations**: Use pathlib for cross-platform

## Error Handling

Layered error handling:

1. **Configuration Errors**: Caught by loader, clear messages
2. **Compilation Errors**: Captured stderr, displayed to user
3. **Linking Errors**: Captured stderr, displayed to user
4. **System Errors**: Try-except with graceful degradation

## Future Enhancements

1. **Precompiled Headers**: Cache compiled headers
2. **Distributed Builds**: Compile across multiple machines
3. **Remote Caching**: Shared cache for teams
4. **IDE Integration**: Generate VSCode/CLion projects
5. **Package Management**: Integrate with Conan/vcpkg
6. **Android/iOS**: Full mobile support
7. **WebAssembly**: Emscripten integration

## Testing Strategy

Test components:
- Unit tests for variable expansion
- Integration tests for build scenarios
- Platform-specific test matrices
- Performance benchmarks

## Security Considerations

- .nken files are Python code (trusted source required)
- No remote code execution
- Sandbox option for untrusted builds
- Hash verification for cache integrity

## Conclusion

Nken provides a modern, efficient build system with:
- Simple configuration syntax
- Fast incremental builds
- Cross-platform support
- Extensible architecture
- Professional output

The modular design allows easy extension and customization for specific project needs.
