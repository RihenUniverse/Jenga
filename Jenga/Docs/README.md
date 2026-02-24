# Jenga Build System v2.0.1

Modern multi-platform C/C++ build system with a unified Python DSL.

[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org)
[![Targets](https://img.shields.io/badge/Targets-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android%20%7C%20iOS%20%7C%20Web%20%7C%20HarmonyOS-green.svg)]()

## Documentation Links

- Main README: [`README.md`](./README.md)
- Complete README: [`READMEV2.md`](./READMEV2.md)
- Wiki: [`wiki/README.md`](./wiki/README.md) (home: [`wiki/Home.md`](./wiki/Home.md))
- User Guide: [`Jenga_User_Guide.md`](./Jenga_User_Guide.md)
- Developer Guide: [`Jenga_Developer_Guide.md`](./Jenga_Developer_Guide.md)

## Overview

Jenga is a build system for native projects, driven by a Python DSL (`.jenga` files) and a CLI.

Current codebase highlights:
- Workspace/project DSL in `Jenga/Core/Api.py`
- CLI commands in `Jenga/Commands/`
- Multi-platform builders in `Jenga/Core/Builders/`
- Built-in test integration (`unitest` + `test` contexts)
- Documentation extraction command (`jenga docs`)
- Toolchain registration/detection workflows (`jenga install toolchain`, `jenga config`)

## Table of Contents

- [Documentation Links](#documentation-links)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [CLI Reference](#cli-reference)
- [Python DSL Reference](#python-dsl-reference)
- [Project Creation and File Management](#project-creation-and-file-management)
- [External Project Integration](#external-project-integration)
- [Toolchains and Sysroots](#toolchains-and-sysroots)
- [Documentation Extraction](#documentation-extraction)
- [Examples](#examples)
- [Known Limitations](#known-limitations)
- [Repository Structure](#repository-structure)
- [License](#license)
- [Disclaimer](#disclaimer)

## Features

### Core Build Features
- Python DSL with context managers: `workspace`, `project`, `toolchain`, `filter`, `unitest`, `test`, `include`, `batchinclude`
- Build graph with project dependencies via `dependson([...])`
- Incremental workflow with cache and daemon support in core commands
- Unified build/run/test/clean/rebuild/watch commands

### Platform and Toolchain Features
- Target model in API: OS, architecture, environment (`TargetOS`, `TargetArch`, `TargetEnv`)
- Builder dispatch for wired platforms: Windows, Linux, macOS, Android, iOS, Web (Emscripten), HarmonyOS, Xbox
- Custom toolchain definitions in DSL (`settarget`, `ccompiler`, `cppcompiler`, `sysroot`, `targettriple`, flags)
- Global toolchain registry management (`jenga install toolchain ...`, `jenga config toolchain ...`)

### Developer Productivity
- Project scaffolding and code element creation (`jenga project`)
- File/include/link/define injection into `.jenga` (`jenga file`)
- Example catalog and copy workflow (`jenga examples list/copy`)
- Project generator command (`jenga gen --cmake --makefile --vs2022 --xcode`)

### Docs and Packaging Commands
- API documentation extraction from source comments (`jenga docs`)
- Packaging, deploy, publish, profile, bench command families available

## Quick Start

### 1) Create a workspace and a project

```bash
mkdir hello-jenga
cd hello-jenga
jenga workspace HelloWorkspace
jenga project HelloApp --kind console --lang C++
```

### 2) Minimal `.jenga` example

```python
from Jenga import *

with workspace("HelloWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX, TargetOS.MACOS])
    targetarchs([TargetArch.X86_64])

    with project("HelloApp"):
        consoleapp()
        language("C++")
        files(["src/**.cpp", "include/**.hpp"])
```

### 3) Build and run

```bash
jenga build --config Debug
jenga run HelloApp
```

## Installation

### From source (recommended for this repository)

```bash
pip install -e .
```

### Launch options

Use one of the following launch paths:

```bash
# Linux/macOS
bash ./jenga.sh --help

# Windows
jenga.bat --help

# Direct Python entry
python3 Jenga/jenga.py --help
```

Dependencies are defined in `pyproject.toml` (`watchdog`, `requests`) and optional extras in `setup.py`.

## CLI Reference

The command registry is defined in `Jenga/Commands/__init__.py`.

### Core workflow

```bash
jenga build   [--config Debug|Release] [--platform <os[-arch[-env]]>] [--target <project>] [--no-cache]
jenga run     [project] [--config Debug] [--platform <platform>] [--args ...] [--no-build]
jenga test    [--project <test-project>] [--config Debug] [--platform <platform>] [--no-build]
jenga clean   [--project <project>] [--config <cfg>] [--platform <platform>] [--all]
jenga rebuild [--config <cfg>] [--platform <platform>] [--target <project>] [--clean-all]
jenga watch   [--config <cfg>] [--platform <platform>] [--polling]
jenga info    [--verbose]
jenga gen     --cmake|--makefile|--vs2022|--xcode [--output <dir>]
```

Common aliases:
- `b` -> `build`
- `r` -> `run`
- `t` -> `test`
- `c` -> `clean`
- `w` -> `watch`
- `i` -> `info`
- `e` -> `examples`
- `d` -> `docs`
- `k` -> `keygen`
- `s` -> `sign`
- `h` -> `help`

### Workspace and project authoring

```bash
jenga workspace [name] [--path .] [--configs Debug,Release] [--oses Windows,Linux,macOS] [--archs x86_64]
jenga project <name> [--kind console|windowed|static|shared|test] [--lang C++|C] [--location .]
jenga project --element class|struct|enum|union|interface|function|source|header|custom \
              --name <ElementName> --project <ProjectName> [--template <template-name>]
jenga file [project] [--src ...] [--inc ...] [--link ...] [--def ...] [--type source|header|resource]
```

### Toolchains and configuration

```bash
jenga install toolchain list
jenga install toolchain detect
jenga install toolchain install zig|emsdk|android-sdk|android-ndk|harmony-sdk|macos-tools \
      [--path <dir_or_archive>] [--version <ver>] [--force]

jenga config init
jenga config show
jenga config set <key> <value>
jenga config get <key>
jenga config toolchain add <name> <json-file>
jenga config toolchain list
jenga config toolchain remove <name>
jenga config sysroot add <name> <path> [--os Linux] [--arch x86_64]
jenga config sysroot list
jenga config sysroot remove <name>
```

### Examples and docs

```bash
jenga examples list [--filter <platform|difficulty>]
jenga examples copy <example-id> <destination> [--force]

jenga docs extract [--project <name>] [--output docs] [--format markdown|html|pdf|all] \
                   [--include-private] [--exclude-projects ...] [--exclude-dirs ...] [--verbose]
jenga docs stats [--project <name>] [--json]
jenga docs list
jenga docs clean [--project <name>] [--output docs]
```

### Distribution and operations

```bash
jenga package --platform android|ios|windows|linux|macos|web [--type <pkg-type>] [--project <name>]
jenga deploy  --platform android|ios|xbox|linux|macos|windows [--target <device>] [--project <name>]
jenga publish --registry nuget|vcpkg|conan|npm|pypi|custom [--package <path>] [--dry-run]
jenga profile --platform windows|linux|macos|android|ios [--project <name>] [--duration 30]
jenga bench   [--project <name>] [--iterations 10] [--output ./bench_results.json]
jenga help [command]
```

## Python DSL Reference

The public DSL is exported from `Jenga/__init__.py` and implemented in `Jenga/Core/Api.py`.

### Minimal workspace and project

```python
from Jenga import *

with workspace("MyWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.WINDOWS, TargetOS.LINUX, TargetOS.MACOS])
    targetarchs([TargetArch.X86_64])
    startproject("App")

    with project("App"):
        consoleapp()
        language("C++")
        cppdialect("C++20")
        files(["src/**.cpp", "include/**.hpp"])
        includedirs(["include"])
```

### Toolchain definition and selection

```python
with workspace("CrossDemo"):
    with toolchain("linux_cross", "clang"):
        settarget("linux", "x64", "gnu")
        targettriple("x86_64-unknown-linux-gnu")
        ccompiler("clang")
        cppcompiler("clang++")
        linker("clang++")
        archiver("ar")
        cflags(["--target=x86_64-unknown-linux-gnu"])
        cxxflags(["--target=x86_64-unknown-linux-gnu"])
        ldflags(["--target=x86_64-unknown-linux-gnu"])

    usetoolchain("linux_cross")
```

### Filters and conditional settings

```python
with project("Renderer"):
    sharedlib()
    files(["src/**.cpp"])

    with filter("system:Windows"):
        links(["d3d11", "dxgi"])
        defines(["PLATFORM_WINDOWS"])

    with filter("system:Linux"):
        links(["X11"])
        defines(["PLATFORM_LINUX"])
```

### Built-in unit testing workflow

```python
with workspace("UnitDemo"):
    with unitest() as u:
        u.Precompiled()  # or u.Compile(...)

    with project("Core"):
        staticlib()
        files(["src/**.cpp"])
        includedirs(["include"])

        with test():
            testfiles(["tests/**.cpp"])
            testmainfile("src/main.cpp")
            testoptions(["--verbose"])
```

### Platform-specific DSL APIs

Android:
- `androidsdkpath`, `androidndkpath`, `javajdkpath`
- `androidapplicationid`, `androidversioncode`, `androidversionname`
- `androidminsdk`, `androidtargetsdk`, `androidcompilesdk`
- `androidabis`, `androidproguard`, `androidproguardrules`
- `androidassets`, `androidpermissions`, `androidnativeactivity`
- `androidsign`, `androidkeystore`, `androidkeystorepass`, `androidkeyalias`

Emscripten:
- `emscriptenshellfile`, `emscriptencanvasid`, `emscripteninitialmemory`
- `emscriptenstacksize`, `emscriptenexportname`, `emscriptenextraflags`

iOS:
- `iosbundleid`, `iosversion`, `iosminsdk`
- `iossigningidentity`, `iosentitlements`, `iosappicon`, `iosbuildnumber`

### Build and linker tuning APIs

- Compile/link flags: `addcflag`, `addcxxflag`, `addldflag`, `cflags`, `cxxflags`, `ldflags`, `asmflags`, `arflags`
- Linking: `framework`, `frameworkpath`, `librarypath`, `library`, `rpath`
- Low-level toggles: `sanitize`, `nostdlib`, `nostdinc`, `pic`, `pie`
- Build metadata: `buildoption`, `buildoptions`

## Project Creation and File Management

### Create projects

```bash
jenga project Game --kind console --lang C++ --location .
jenga project Engine --kind static --lang C++
jenga project Tools --kind shared --lang C++
```

### Create code elements in existing project

```bash
jenga project --element class --name Player --project Game
jenga project --element struct --name Vec3 --project Engine
jenga project --element enum --name ErrorCode --project Engine
jenga project --element custom --name config.json --project Game --template json
```

### Update `.jenga` quickly

```bash
jenga file Game --src src/new_system.cpp
jenga file Game --inc third_party/include
jenga file Game --link opengl32
jenga file Game --def ENABLE_LOGS=1
```

## External Project Integration

The API includes external workspace inclusion and introspection helpers.

### Include one external `.jenga`

```python
with workspace("App"):
    with include("libs/math/math.jenga") as inc:
        inc.only(["MathLib"])  # or inc.skip(["Tests"])

    with project("AppMain"):
        consoleapp()
        dependson(["MathLib"])
```

### Include multiple files

```python
with workspace("App"):
    with batchinclude([
        "libs/logger/logger.jenga",
        "libs/math/math.jenga",
    ]):
        pass
```

### Introspection helpers

- `useproject(projectname, copyincludes=True, copydefines=True)`
- `getprojectproperties(projectname=None)`
- `includefromdirectory(directory, pattern="*.jenga")`
- `listincludes()`, `getincludeinfo(projectname)`, `validateincludes()`
- `getincludedprojects()`, `generatedependencyreport("DEPENDENCIES.md")`, `listallprojects()`

## Toolchains and Sysroots

### DSL-level custom tool definitions

- `CreateAndroidNdkTool(ndkPath, apiLevel=21, arch="arm64-v8a")`
- `CreateEmscriptenTool(emsdkPath)`
- `CreateCustomGccTool(gccPath, version="")`

### Tool registry helpers

- `addtools(...)` context
- `usetool(name)`, `listtools()`, `gettoolinfo(name)`, `validatetools()`

### Sysroot setup helper script

Repository includes `scripts/setup_linux_sysroot.py` to bootstrap a Linux sysroot for cross-compilation scenarios.

## Documentation Extraction

`jenga docs` is implemented in `Jenga/Commands/Docs.py`.

### Supported source comment forms in extractor

- Block comments: `/** ... */`
- Line comments: `/// ...`
- Doxygen-style tags parsing for:
  - `@brief`
  - `@param`
  - `@tparam`
  - `@return`, `@retval`
  - `@throws`
  - `@example`, `@code ... @endcode`
  - `@note`, `@warning`, `@see`
  - `@since`, `@deprecated`, `@author`, `@date`, `@complexity`

### Typical usage

```bash
jenga docs extract
jenga docs extract --project NKFramework --include-private --verbose
jenga docs list
jenga docs stats
jenga docs clean
```

### Generated markdown structure

```text
docs/
  <ProjectName>/
    markdown/
      index.md
      api.md
      search.md
      stats.md
      files/
      namespaces/
      types/
```

## Examples

The `Exemples/` directory contains ready-to-use workspaces, including:

- `01_hello_console`
- `02_static_library`
- `03_shared_library`
- `04_unit_tests`
- `05_android_ndk`
- `07_web_wasm`
- `14_cross_compile`
- `21_zig_cross_compile`
- `22_nk_multiplatform_sandbox`

Use:

```bash
jenga examples list
jenga examples copy 01_hello_console ./hello_copy
```

## Known Limitations

Current command/API surface is broad, but some parts are partial in code:

- `jenga docs`:
  - `--format html|pdf|all` is accepted, but generator currently implements markdown output path.
  - `docs stats` currently prints minimal workspace-level stats.
- `jenga publish`:
  - NuGet flow is implemented.
  - vcpkg/conan/npm/pypi/custom paths are placeholders.
- `jenga profile`:
  - Linux has a partial `perf` flow.
  - Other platform implementations are mostly placeholders.
- `jenga deploy`:
  - Android/iOS/Xbox paths exist.
  - Linux deploy is marked as not implemented.
- Advanced packaging types depend on builder/tool availability on host system.

## Repository Structure

```text
Jenga/
  Commands/          # CLI commands
  Core/              # DSL, loader, cache, builder core
  Core/Builders/     # Platform builders
  Utils/             # Utilities
  Unitest/           # Built-in C++ unit test framework assets
Exemples/            # Sample projects
scripts/             # Utility scripts (sysroot, wrappers)
templates/           # Toolchain templates
jenga.sh / jenga.bat # CLI launchers
```

## License

Proprietary License.

See repository policy and distribution terms defined by the project owner.

## Disclaimer

This software is provided "as is", without warranty of any kind.
Use in production requires validation in your own toolchain and target environment.
