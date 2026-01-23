"""
Jenga Build System API Stub File
This file provides type hints for IDE auto-completion in .jenga files

Usage:
  In your .jenga file, add at the top:
  # type: ignore
  from jenga_stubs import *
  
  This will give you IntelliSense without affecting runtime
"""

from typing import List, Union

# Context Managers
class workspace:
    """Workspace configuration context"""
    def __init__(self, name: str): ...
    def __enter__(self): ...
    def __exit__(self, *args): ...

class project:
    """Project configuration context"""
    def __init__(self, name: str): ...
    def __enter__(self): ...
    def __exit__(self, *args): ...

class toolchain:
    """Toolchain configuration context"""
    def __init__(self, name: str, compiler: str): ...
    def __enter__(self): ...
    def __exit__(self, *args): ...

class filter:
    """Filter configuration for platform/config-specific settings"""
    def __init__(self, condition: str): ...
    def __enter__(self): ...
    def __exit__(self, *args): ...

class test:
    """Test project configuration context"""
    def __init__(self, name: str): ...
    def __enter__(self): ...
    def __exit__(self, *args): ...

# Workspace Configuration
def configurations(configs: List[str]) -> None:
    """Set build configurations (e.g., Debug, Release, Dist)"""
    ...

def platforms(platforms_list: List[str]) -> None:
    """Set target platforms (e.g., Windows, Linux, MacOS, Android, iOS)"""
    ...

def startproject(name: str) -> None:
    """Set the startup project"""
    ...

def location(path: str) -> None:
    """Set project or workspace location"""
    ...

# Project Kinds
def consoleapp() -> None:
    """Set project kind to console application"""
    ...

def windowedapp() -> None:
    """Set project kind to windowed application"""
    ...

def staticlib() -> None:
    """Set project kind to static library"""
    ...

def sharedlib() -> None:
    """Set project kind to shared/dynamic library"""
    ...

def testsuite() -> None:
    """Set project kind to test suite"""
    ...

# Language Settings
def language(lang: str) -> None:
    """Set programming language (C, C++, C#, etc.)"""
    ...

def cppdialect(standard: str) -> None:
    """Set C++ standard (C++11, C++14, C++17, C++20, C++23)"""
    ...

def cdialect(standard: str) -> None:
    """Set C standard (C89, C99, C11, C17)"""
    ...

# Files
def files(patterns: List[str]) -> None:
    """
    Add source files with wildcard support
    Examples: 
      files(["src/**.cpp", "include/**.h"])
      files(["/src/**.cpp"])  # Relative to project location
    """
    ...

def excludefiles(patterns: List[str]) -> None:
    """
    Exclude files from build
    Examples:
      excludefiles(["!old_code.cpp", "!deprecated/**"])
    """
    ...

def excludemainfiles(patterns: List[str]) -> None:
    """Exclude main files (for test projects)"""
    ...

# Directories
def includedirs(dirs: List[str]) -> None:
    """
    Add include directories
    Examples:
      includedirs(["%{wks.location}/include", "%{Core.location}/src"])
    """
    ...

def libdirs(dirs: List[str]) -> None:
    """Add library directories"""
    ...

def objdir(path: str) -> None:
    """
    Set object files directory
    Example: objdir("%{wks.location}/Build/Obj/%{cfg.buildcfg}/%{prj.name}")
    """
    ...

def targetdir(path: str) -> None:
    """
    Set output directory for built target
    Example: targetdir("%{wks.location}/Build/Bin/%{cfg.buildcfg}")
    """
    ...

def targetname(name: str) -> None:
    """Set output file name (without extension)"""
    ...

# Linking
def links(libraries: List[str]) -> None:
    """
    Link with libraries
    Examples:
      links(["pthread", "dl", "m"])
      links(["kernel32", "user32"])
    """
    ...

def dependson(projects: List[str]) -> None:
    """
    Add project dependencies
    Example: dependson(["Core", "Logger"])
    """
    ...

# File Dependencies and Resources
def dependfiles(patterns: List[str]) -> None:
    """
    Copy files to output directory after build
    Examples:
      dependfiles(["assets/**", "config/*.json", "libs/*.dll"])
    """
    ...

def embedresources(files: List[str]) -> None:
    """
    Embed resources into executable
    Examples:
      embedresources(["icon.ico", "manifest.xml", "resources.rc"])
    """
    ...

# Compiler Settings
def defines(defs: List[str]) -> None:
    """
    Add preprocessor defines
    Example: defines(["DEBUG", "_DEBUG", "MY_DEFINE=1"])
    """
    ...

def optimize(level: str) -> None:
    """
    Set optimization level
    Options: Off, On, Debug, Size, Speed, Full
    """
    ...

def symbols(enable: Union[bool, str]) -> None:
    """
    Enable/disable debug symbols
    Options: On, Off, FastLink, Full
    """
    ...

def warnings(level: str) -> None:
    """
    Set warning level
    Options: Off, Default, Extra, High, Everything
    """
    ...

# Build Hooks
def prebuild(commands: List[str]) -> None:
    """
    Execute commands before build starts
    Example: prebuild(["echo Starting build...", "python generate_version.py"])
    """
    ...

def postbuild(commands: List[str]) -> None:
    """
    Execute commands after build completes
    Example: postbuild(["echo Build complete!", "cp assets/* %{prj.targetdir}/"])
    """
    ...

def prelink(commands: List[str]) -> None:
    """Execute commands before linking"""
    ...

def postlink(commands: List[str]) -> None:
    """Execute commands after linking"""
    ...

# Toolchain Selection
def usetoolchain(name: str) -> None:
    """
    Select toolchain for this project
    Example: usetoolchain("gcc")
    """
    ...

# Android Settings
def androidsdkpath(path: str) -> None:
    """Set Android SDK path"""
    ...

def androidndkpath(path: str) -> None:
    """Set Android NDK path"""
    ...

def javajdkpath(path: str) -> None:
    """Set Java JDK path"""
    ...

def androidapplicationid(app_id: str) -> None:
    """
    Set Android application ID
    Example: androidapplicationid("com.mycompany.myapp")
    """
    ...

def androidversioncode(code: int) -> None:
    """Set Android version code (integer)"""
    ...

def androidversionname(name: str) -> None:
    """Set Android version name (string)"""
    ...

def androidminsdk(version: int) -> None:
    """Set minimum Android SDK version"""
    ...

def androidtargetsdk(version: int) -> None:
    """Set target Android SDK version"""
    ...

def androidsign(enable: bool = True) -> None:
    """Enable APK signing"""
    ...

def androidkeystore(path: str) -> None:
    """Set keystore file path for APK signing"""
    ...

def androidkeystorepass(password: str) -> None:
    """Set keystore password"""
    ...

def androidkeyalias(alias: str) -> None:
    """Set key alias for APK signing"""
    ...

# Test Settings
def testoptions(options: List[str]) -> None:
    """Set test framework options"""
    ...

# Test Settings
def testoptions(options: List[str]) -> None:
    """
    Add test options (command-line arguments for test runner)
    Examples:
      testoptions(["--verbose", "--filter=MyTest*", "--parallel"])
    """
    ...

def testfiles(patterns: List[str]) -> None:
    """
    Specify test files location
    Example: testfiles(["tests/**.cpp"])
    """
    ...

def testmainfile(main_file: str) -> None:
    """
    Specify the application's main file to exclude from test build
    Example: testmainfile("src/main.cpp")
    """
    ...

def testmaintemplate(template_file: str) -> None:
    """
    Specify custom test main template
    Example: testmaintemplate("custom_test_main.cpp")
    """
    ...

# Precompiled Headers
def pchheader(header: str) -> None:
    """
    Set precompiled header file
    Example: pchheader("pch.h")
    """
    ...

def pchsource(source: str) -> None:
    """
    Set precompiled header source file
    Example: pchsource("pch.cpp")
    """
    ...

# Other
def systemversion(version: str) -> None:
    """Set system version (for macOS/iOS)"""
    ...

# Toolchain Settings
def cppcompiler(path: str) -> None:
    """Set C++ compiler path"""
    ...

def ccompiler(path: str) -> None:
    """Set C compiler path"""
    ...

def toolchaindir(path: str) -> None:
    """Set toolchain directory"""
    ...
