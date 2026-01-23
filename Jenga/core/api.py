#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Core API
Provides the DSL for configuring workspaces and projects
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
from enum import Enum


class ProjectKind(Enum):
    """Project types"""
    CONSOLE_APP = "ConsoleApp"
    WINDOWED_APP = "WindowedApp"
    STATIC_LIB = "StaticLib"
    SHARED_LIB = "SharedLib"
    TEST_SUITE = "TestSuite"


class Language(Enum):
    """Programming languages"""
    C = "C"
    CPP = "C++"
    OBJC = "Objective-C"
    OBJCPP = "Objective-C++"


class Optimization(Enum):
    """Optimization levels"""
    OFF = "Off"
    SIZE = "Size"
    SPEED = "Speed"
    FULL = "Full"


@dataclass
class Toolchain:
    """Toolchain configuration"""
    name: str
    compiler: str
    ccompiler: Optional[str] = None
    cppcompiler: Optional[str] = None
    linker: Optional[str] = None
    archiver: Optional[str] = None
    sysroot: Optional[str] = None
    targettriple: Optional[str] = None
    
    # Explicit paths to compilers
    compiler_path: Optional[str] = None
    ccompiler_path: Optional[str] = None
    cppcompiler_path: Optional[str] = None
    linker_path: Optional[str] = None
    archiver_path: Optional[str] = None
    
    # Toolchain root directory
    toolchain_dir: Optional[str] = None
    
    defines: List[str] = field(default_factory=list)
    flags: Dict[str, List[str]] = field(default_factory=dict)
    cflags: List[str] = field(default_factory=list)
    cxxflags: List[str] = field(default_factory=list)
    ldflags: List[str] = field(default_factory=list)


@dataclass
class Project:
    """Project configuration"""
    name: str
    kind: ProjectKind = ProjectKind.CONSOLE_APP
    language: Language = Language.CPP
    location: str = ""  # Now mandatory for projects
    cppdialect: str = "C++17"
    cdialect: str = "C11"
    
    # Files
    files: List[str] = field(default_factory=list)
    excludefiles: List[str] = field(default_factory=list)
    excludemainfiles: List[str] = field(default_factory=list)
    
    # Precompiled Headers
    pchheader: str = ""  # Header to precompile (e.g., "pch.h")
    pchsource: str = ""  # Source file for PCH (e.g., "pch.cpp")
    
    # Directories
    includedirs: List[str] = field(default_factory=list)
    libdirs: List[str] = field(default_factory=list)
    
    # Build settings
    objdir: str = ""
    targetdir: str = ""
    targetname: str = ""
    
    # Dependencies
    links: List[str] = field(default_factory=list)
    dependson: List[str] = field(default_factory=list)
    
    # File dependencies (copy to output after build)
    dependfiles: List[str] = field(default_factory=list)  # Files/folders to copy
    
    # Embedded resources (compiled into executable)
    embedresources: List[str] = field(default_factory=list)  # Resources to embed
    
    # Compiler settings
    defines: List[str] = field(default_factory=list)
    optimize: Optimization = Optimization.OFF
    symbols: bool = True
    warnings: str = "Default"
    
    # Toolchain
    toolchain: Optional[str] = None  # Specific toolchain for this project
    _explicit_toolchain = False  # Track si le toolchain est explicitement défini
        
    # Build hooks
    prebuildcommands: List[str] = field(default_factory=list)
    postbuildcommands: List[str] = field(default_factory=list)
    prelinkcommands: List[str] = field(default_factory=list)
    postlinkcommands: List[str] = field(default_factory=list)
    
    # Platform-specific
    system_defines: Dict[str, List[str]] = field(default_factory=dict)
    system_links: Dict[str, List[str]] = field(default_factory=dict)
    
    # Android specific
    androidapplicationid: str = ""
    androidversioncode: int = 1
    androidversionname: str = "1.0"
    androidminsdk: int = 21
    androidtargetsdk: int = 33
    androidsign: bool = False  # Sign APK
    androidkeystore: str = ""  # Path to keystore
    androidkeystorepass: str = ""  # Keystore password
    androidkeyalias: str = ""  # Key alias
    
    # Test settings
    is_test: bool = False
    parent_project: Optional[str] = None
    testoptions: List[str] = field(default_factory=list)
    testfiles: List[str] = field(default_factory=list)  # Test source files location
    testmainfile: str = ""  # Main file to exclude from test build
    testmaintemplate: str = ""  # Template main for tests (auto-injected)
    
    # Current filter context
    _current_filter: Optional[str] = None
    _filtered_defines: Dict[str, List[str]] = field(default_factory=dict)
    _filtered_optimize: Dict[str, Optimization] = field(default_factory=dict)
    _filtered_symbols: Dict[str, bool] = field(default_factory=dict)


@dataclass
class Workspace:
    """Workspace configuration"""
    name: str
    location: str = ""
    configurations: List[str] = field(default_factory=lambda: ["Debug", "Release"])
    platforms: List[str] = field(default_factory=lambda: ["Windows"])
    startproject: str = ""
    projects: Dict[str, Project] = field(default_factory=dict)
    toolchains: Dict[str, Toolchain] = field(default_factory=dict)
        
    toolchain = None  # Toolchain par défaut pour tous les projets
    
    # Android SDK/NDK paths
    androidsdkpath: str = ""
    androidndkpath: str = ""
    javajdkpath: str = ""
    
    # Current context
    _current_project: Optional[Project] = None
    _current_toolchain: Optional[Toolchain] = None


# Global state
_current_workspace: Optional[Workspace] = None
_current_project: Optional[Project] = None
_current_toolchain: Optional[Toolchain] = None
_current_filter: Optional[str] = None


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class workspace:
    """Workspace context manager"""
    def __init__(self, name: str):
        self.workspace = Workspace(name=name)
        
    def __enter__(self):
        global _current_workspace
        _current_workspace = self.workspace
        
        # AUTOMATIC: Inject Unitest as hidden backend library
        self._inject_unitest_backend()
        
        return self.workspace
    
    def _inject_unitest_backend(self):
        """Automatically add Unitest as a static library (hidden from user)"""
        from pathlib import Path
        
        # Create hidden Unitest project
        unitest_proj = Project(name="__Unitest__")
        unitest_proj.kind = ProjectKind.STATIC_LIB
        unitest_proj.language = Language.CPP
        unitest_proj.cppdialect = "C++20"
        
        # Location: Tools/Jenga/Unitest/ (note: lowercase 'Jenga')
        tools_dir = Path(__file__).parent.parent
        unitest_location = tools_dir / "Unitest"
        
        # Fallback: try workspace Unitest/ if Tools/jenga/Unitest doesn't exist
        if not unitest_location.exists():
            # Try workspace root Unitest/
            unitest_location = Path(self.workspace.location if self.workspace.location else ".") / "Unitest"
        
        unitest_proj.location = str(unitest_location)
        
        # Files - adjust pattern to match actual structure
        unitest_proj.files = [f"{unitest_proj.location}/src/Unitest/**.cpp", f"{unitest_proj.location}/src/Unitest/**.h"]
        unitest_proj.includedirs = [f"{unitest_proj.location}/src"]
        
        # Output
        unitest_proj.targetdir = "%{wks.location}/Build/Lib/%{cfg.buildcfg}"
        unitest_proj.objdir = "%{wks.location}/Build/Obj/%{cfg.buildcfg}/__Unitest__"
        unitest_proj.targetname = "__Unitest__"
        
        # Add to workspace (hidden with __ prefix)
        self.workspace.projects["__Unitest__"] = unitest_proj
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_workspace
        # DON'T clear workspace - keep it available for commands
        # _current_workspace = None  # REMOVED
        return False


class project:
    """Project context manager"""
    def __init__(self, name: str):
        self.name = name
        self.project = None
        
    def __enter__(self):
        global _current_workspace, _current_project
        
        if _current_workspace is None:
            raise RuntimeError("Project must be defined within a workspace")
        
        self.project = Project(name=self.name)
        
        # MANDATORY: Set default location to "." (current workspace dir)
        self.project.location = "."
        
        # MANDATORY: Set default toolchain if not specified
        if not self.project.toolchain and _current_workspace.toolchains:
            # Use 'default' toolchain if exists, otherwise first available
            if 'default' in _current_workspace.toolchains:
                self.project.toolchain = 'default'
            else:
                self.project.toolchain = list(_current_workspace.toolchains.keys())[0]
        
        _current_workspace.projects[self.name] = self.project
        _current_project = self.project
        
        return self.project
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_project
        _current_project = None
        return False


class toolchain:
    """Toolchain context manager"""
    def __init__(self, name: str, compiler: str):
        self.name = name
        self.compiler = compiler
        self.toolchain_obj = None
        
    def __enter__(self):
        global _current_workspace, _current_toolchain
        
        if _current_workspace is None:
            raise RuntimeError("Toolchain must be defined within a workspace")
        
        self.toolchain_obj = Toolchain(name=self.name, compiler=self.compiler)
        _current_workspace.toolchains[self.name] = self.toolchain_obj
        _current_toolchain = self.toolchain_obj
        
        return self.toolchain_obj
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_toolchain
        _current_toolchain = None
        return False


class filter:
    """Filter context manager for conditional settings"""
    def __init__(self, filter_expr: str):
        self.filter_expr = filter_expr
        self.previous_filter = None
        
    def __enter__(self):
        global _current_filter, _current_project
        
        self.previous_filter = _current_filter
        _current_filter = self.filter_expr
        
        if _current_project:
            _current_project._current_filter = self.filter_expr
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_filter, _current_project
        
        _current_filter = self.previous_filter
        
        if _current_project:
            _current_project._current_filter = self.previous_filter
        
        return False


class test:
    """Test suite context manager - Creates a test project automatically"""
    def __init__(self, name: str):
        self.name = name
        self.project = None
        self.parent_project = None
        
    def __enter__(self):
        global _current_workspace, _current_project
        
        if _current_workspace is None:
            raise RuntimeError("Test must be defined within a workspace")
        
        # Get the parent project (last defined project before test)
        if _current_project and not _current_project.is_test:
            self.parent_project = _current_project
        else:
            # Find the last non-test project
            for proj_name in reversed(list(_current_workspace.projects.keys())):
                proj = _current_workspace.projects[proj_name]
                if not proj.is_test and not proj_name.startswith("__"):
                    self.parent_project = proj
                    break
        
        if not self.parent_project:
            raise RuntimeError("Test must be defined after a project")
        
        # Create test project based on parent
        test_name = f"{self.parent_project.name}_Tests"
        self.project = Project(name=test_name)
        self.project.kind = ProjectKind.CONSOLE_APP  # Test executable
        self.project.language = self.parent_project.language
        self.project.cppdialect = self.parent_project.cppdialect
        self.project.cdialect = self.parent_project.cdialect
        
        # Mark as test
        self.project.is_test = True
        self.project.parent_project = self.parent_project.name
        
        # Set default location
        self.project.location = "."
        
        # AUTOMATIC: Add dependencies
        # 1. Parent project (to access its code)
        self.project.dependson = [self.parent_project.name]
        
        # 2. Unitest framework (hidden dependency)
        if "__Unitest__" in _current_workspace.projects:
            self.project.dependson.append("__Unitest__")
        
        # Copy includes from parent
        self.project.includedirs = list(self.parent_project.includedirs)
        
        # Add Unitest includes
        import os
        from pathlib import Path
        tools_dir = Path(__file__).parent.parent
        unitest_include = str(tools_dir / "Jenga" / "Unitest" / "src")
        self.project.includedirs.append(unitest_include)
        
        # Set output directories
        self.project.targetdir = "%{wks.location}/Build/Tests/%{cfg.buildcfg}"
        self.project.objdir = "%{wks.location}/Build/Obj/%{cfg.buildcfg}/%{prj.name}"
        
        # Add to workspace
        _current_workspace.projects[test_name] = self.project
        _current_project = self.project
        
        return self.project
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_project
        
        # AUTOMATIC: Inject test main if not provided
        if not self.project.testmaintemplate:
            # Use built-in Unitest main template
            from pathlib import Path
            tools_dir = Path(__file__).parent.parent
            template_path = tools_dir / "Jenga" / "Unitest" / "AutoMainTemplate" / "test_main.cpp"
            if template_path.exists():
                self.project.testmaintemplate = str(template_path)
        
        _current_project = None
        return False


# ============================================================================
# API FUNCTIONS
# ============================================================================

def configurations(configs: List[str]):
    """Set workspace configurations"""
    if _current_workspace:
        _current_workspace.configurations = configs


def platforms(plats: List[str]):
    """Set workspace platforms"""
    if _current_workspace:
        _current_workspace.platforms = plats


def startproject(name: str):
    """Set startup project"""
    if _current_workspace:
        _current_workspace.startproject = name


def location(loc: str):
    """Set location"""
    if _current_project:
        _current_project.location = loc
    elif _current_workspace:
        _current_workspace.location = loc


# Project kind functions
def consoleapp():
    """Set project as console application"""
    if _current_project:
        _current_project.kind = ProjectKind.CONSOLE_APP


def windowedapp():
    """Set project as windowed application"""
    if _current_project:
        _current_project.kind = ProjectKind.WINDOWED_APP


def staticlib():
    """Set project as static library"""
    if _current_project:
        _current_project.kind = ProjectKind.STATIC_LIB


def sharedlib():
    """Set project as shared library"""
    if _current_project:
        _current_project.kind = ProjectKind.SHARED_LIB


def testsuite():
    """Set project as test suite"""
    if _current_project:
        _current_project.kind = ProjectKind.TEST_SUITE
        _current_project.is_test = True


# Language functions
def language(lang: str):
    """Set project language"""
    if _current_project:
        _current_project.language = Language[lang.upper().replace("+", "P").replace("-", "")]


def cppdialect(dialect: str):
    """Set C++ standard"""
    if _current_project:
        _current_project.cppdialect = dialect


def cdialect(dialect: str):
    """Set C standard"""
    if _current_project:
        _current_project.cdialect = dialect


# Project location
def location(path: str):
    """
    Set project location - can be absolute or relative to workspace
    Examples:
      location(".")                           # Current workspace dir (default)
      location("modules/logger")              # Relative to workspace
      location("/home/user/projects/logger")  # Absolute path
    
    When using relative paths with "/" prefix (like "/src/**.cpp"), 
    they are relative to this project location, not the workspace.
    """
    if _current_project:
        from pathlib import Path
        
        # Check if absolute path
        if Path(path).is_absolute():
            _current_project.location = path
        else:
            # Relative to workspace
            _current_project.location = path


# File functions
def files(file_list: List[str]):
    """Add source files"""
    if _current_project:
        _current_project.files.extend(file_list)


def excludefiles(file_list: List[str]):
    """Exclude files"""
    if _current_project:
        _current_project.excludefiles.extend(file_list)


def excludemainfiles(file_list: List[str]):
    """Exclude main files (for tests)"""
    if _current_project:
        _current_project.excludemainfiles.extend(file_list)


# Directory functions
def includedirs(dirs: List[str]):
    """Add include directories"""
    if _current_project:
        _current_project.includedirs.extend(dirs)


def libdirs(dirs: List[str]):
    """Add library directories"""
    if _current_project:
        _current_project.libdirs.extend(dirs)


def objdir(dir_path: str):
    """Set object directory"""
    if _current_project:
        _current_project.objdir = dir_path


def targetdir(dir_path: str):
    """Set target directory"""
    if _current_project:
        _current_project.targetdir = dir_path


def targetname(name: str):
    """Set target name"""
    if _current_project:
        _current_project.targetname = name


# Linking functions
def links(link_list: List[str]):
    """Add libraries to link"""
    if _current_project:
        if _current_filter and "system:" in _current_filter:
            system = _current_filter.split(":")[1]
            if system not in _current_project.system_links:
                _current_project.system_links[system] = []
            _current_project.system_links[system].extend(link_list)
        else:
            _current_project.links.extend(link_list)


def dependson(deps: List[str]):
    """Add project dependencies"""
    if _current_project:
        _current_project.dependson.extend(deps)


# Compiler settings
def defines(defs: List[str]):
    """Add preprocessor defines"""
    if _current_toolchain:
        _current_toolchain.defines.extend(defs)
    elif _current_project:
        if _current_filter:
            if _current_filter not in _current_project._filtered_defines:
                _current_project._filtered_defines[_current_filter] = []
            _current_project._filtered_defines[_current_filter].extend(defs)
        else:
            _current_project.defines.extend(defs)


def optimize(level: str):
    """Set optimization level"""
    if _current_project:
        opt = Optimization[level.upper()]
        if _current_filter:
            _current_project._filtered_optimize[_current_filter] = opt
        else:
            _current_project.optimize = opt


def symbols(enable: str):
    """Enable/disable debug symbols"""
    if _current_project:
        sym = enable.lower() in ["on", "true", "yes"]
        if _current_filter:
            _current_project._filtered_symbols[_current_filter] = sym
        else:
            _current_project.symbols = sym


def warnings(level: str):
    """Set warning level"""
    if _current_project:
        _current_project.warnings = level


# Android settings
def androidsdkpath(path: str):
    """Set Android SDK path"""
    if _current_workspace:
        _current_workspace.androidsdkpath = path


def androidndkpath(path: str):
    """Set Android NDK path"""
    if _current_workspace:
        _current_workspace.androidndkpath = path


def javajdkpath(path: str):
    """Set Java JDK path"""
    if _current_workspace:
        _current_workspace.javajdkpath = path


def androidapplicationid(app_id: str):
    """Set Android application ID"""
    if _current_project:
        _current_project.androidapplicationid = app_id


def androidversioncode(code: int):
    """Set Android version code"""
    if _current_project:
        _current_project.androidversioncode = code


def androidversionname(name: str):
    """Set Android version name"""
    if _current_project:
        _current_project.androidversionname = name


def androidminsdk(sdk: int):
    """Set Android minimum SDK"""
    if _current_project:
        _current_project.androidminsdk = sdk


def androidtargetsdk(sdk: int):
    """Set Android target SDK"""
    if _current_project:
        _current_project.androidtargetsdk = sdk


# Test settings
def testoptions(opts: List[str]):
    """
    Set test options (command-line arguments)
    Example: testoptions(["--verbose", "--filter=MyTest*"])
    """
    if _current_project:
        _current_project.testoptions.extend(opts)


def testfiles(patterns: List[str]):
    """
    Specify test files location
    Example: testfiles(["tests/**.cpp"])
    """
    if _current_project:
        _current_project.testfiles.extend(patterns)


def testmainfile(main_file: str):
    """
    Specify the application's main file to exclude from test build
    Example: testmainfile("src/main.cpp")
    """
    if _current_project:
        _current_project.testmainfile = main_file


def testmaintemplate(template_file: str):
    """
    Specify custom test main template
    If not specified, uses Unitest/AutoMainTemplate/test_main.cpp
    Example: testmaintemplate("custom_test_main.cpp")
    """
    if _current_project:
        _current_project.testmaintemplate = template_file


def systemversion(version: str):
    """Set system version (for Windows)"""
    # This is typically handled by the build system
    pass


# Toolchain settings
def cppcompiler(compiler_path: str):
    """Set C++ compiler path"""
    if _current_toolchain:
        _current_toolchain.cppcompiler = compiler_path
        _current_toolchain.cppcompiler_path = compiler_path


def ccompiler(compiler_path: str):
    """Set C compiler path"""
    if _current_toolchain:
        _current_toolchain.ccompiler = compiler_path
        _current_toolchain.ccompiler_path = compiler_path


def toolchaindir(path: str):
    """Set toolchain root directory"""
    if _current_toolchain:
        _current_toolchain.toolchain_dir = path


# Build hooks
def prebuild(commands: List[str]):
    """Add pre-build commands"""
    if _current_project:
        _current_project.prebuildcommands.extend(commands)


def postbuild(commands: List[str]):
    """Add post-build commands"""
    if _current_project:
        _current_project.postbuildcommands.extend(commands)


def prelink(commands: List[str]):
    """Add pre-link commands"""
    if _current_project:
        _current_project.prelinkcommands.extend(commands)


def postlink(commands: List[str]):
    """Add post-link commands"""
    if _current_project:
        _current_project.postlinkcommands.extend(commands)


# Project toolchain selection
def usetoolchain(name: str):
    """
    Use a specific toolchain
    
    When called in workspace: sets default for all projects
    When called in project: overrides workspace default
    """
    global _current_project, _current_workspace
    
    # Si on est dans un projet
    if _current_project is not None:
        if name not in _current_workspace.toolchains:
            raise ValueError(f"Toolchain '{name}' not defined")
        
        _current_project.toolchain = name
        _current_project._explicit_toolchain = True  # Marquer comme explicite
    
    # Si on est dans un workspace (mais pas dans un projet)
    elif _current_workspace is not None:
        if name not in _current_workspace.toolchains:
            raise ValueError(f"Toolchain '{name}' not defined. Define it first.")
        
        _current_workspace.toolchain = name
        
        # Appliquer à tous les projets existants sans toolchain explicite
        for project in _current_workspace.projects.values():
            if not hasattr(project, '_explicit_toolchain') or not project._explicit_toolchain:
                project.toolchain = name
    
    else:
        raise RuntimeError("usetoolchain() must be called within a workspace or project")


# File dependencies
def dependfiles(patterns: List[str]):
    """
    Add file/folder dependencies to copy after build
    Example: dependfiles(["assets/**", "config/*.json", "libs/*.dll"])
    """
    if _current_project:
        _current_project.dependfiles.extend(patterns)


# Precompiled Headers
def pchheader(header: str):
    """
    Set precompiled header file
    Example: pchheader("pch.h")
    """
    if _current_project:
        _current_project.pchheader = header


def pchsource(source: str):
    """
    Set precompiled header source file
    Example: pchsource("pch.cpp")
    """
    if _current_project:
        _current_project.pchsource = source


# Embedded resources
def embedresources(resources: List[str]):
    """
    Add resources to embed in executable
    Example: embedresources(["icon.ico", "manifest.xml", "resources.rc"])
    """
    if _current_project:
        _current_project.embedresources.extend(resources)


# Android signing
def androidsign(enable: bool = True):
    """Enable APK signing for Android"""
    if _current_project:
        _current_project.androidsign = enable


def androidkeystore(path: str):
    """Set Android keystore path"""
    if _current_project:
        _current_project.androidkeystore = path


def androidkeystorepass(password: str):
    """Set Android keystore password"""
    if _current_project:
        _current_project.androidkeystorepass = password


def androidkeyalias(alias: str):
    """Set Android key alias"""
    if _current_project:
        _current_project.androidkeyalias = alias


# Helper function to get current workspace
def get_current_workspace() -> Optional[Workspace]:
    """Get the current workspace"""
    return _current_workspace


def reset_state():
    """Reset global state (for testing)"""
    global _current_workspace, _current_project, _current_toolchain, _current_filter
    _current_workspace = None
    _current_project = None
    _current_toolchain = None
    _current_filter = None

# ============================================================================
# ADVANCED TOOLCHAIN FUNCTIONS
# ============================================================================

def addflag(flag: str):
    """Add a single flag to current toolchain"""
    if _current_toolchain:
        if _current_filter:
            filter_type = _current_filter.split(":")[0]
            if filter_type not in _current_toolchain.flags:
                _current_toolchain.flags[filter_type] = []
            _current_toolchain.flags[filter_type].append(flag)
        else:
            if flag.startswith("-l") or flag.startswith("-L"):
                _current_toolchain.ldflags.append(flag)
            elif flag.startswith("-D"):
                _current_toolchain.defines.append(flag[2:])
            else:
                _current_toolchain.cflags.append(flag)

def addcflag(flag: str):
    """Add a single C-specific flag"""
    if _current_toolchain:
        _current_toolchain.cflags.append(flag)

def addcxxflag(flag: str):
    """Add a single C++-specific flag"""
    if _current_toolchain:
        _current_toolchain.cxxflags.append(flag)

def addldflag(flag: str):
    """Add a single linker flag"""
    if _current_toolchain:
        _current_toolchain.ldflags.append(flag)

def adddefine(define: str):
    """Add a single preprocessor define"""
    if _current_toolchain:
        _current_toolchain.defines.append(define)

def framework(framework_name: str):
    """Add framework (macOS specific)"""
    if _current_toolchain:
        if _current_filter and "system:MacOS" in _current_filter:
            _current_toolchain.ldflags.append(f"-framework {framework_name}")
        else:
            if "macos_frameworks" not in _current_toolchain.flags:
                _current_toolchain.flags["macos_frameworks"] = []
            _current_toolchain.flags["macos_frameworks"].append(framework_name)

def librarypath(path: str):
    """Add library search path (-L)"""
    if _current_toolchain:
        _current_toolchain.ldflags.append(f"-L{path}")

def library(lib_name: str):
    """Add library to link (-l)"""
    if _current_toolchain:
        _current_toolchain.ldflags.append(f"-l{lib_name}")

def rpath(path: str):
    """Add runtime library path (-rpath)"""
    if _current_toolchain:
        _current_toolchain.ldflags.append(f"-Wl,-rpath,{path}")

def nostdlib():
    """Do not use standard system libraries"""
    if _current_toolchain:
        _current_toolchain.ldflags.append("-nostdlib")

def nostdinc():
    """Do not use standard system includes"""
    if _current_toolchain:
        _current_toolchain.cflags.append("-nostdinc")
        _current_toolchain.cxxflags.append("-nostdinc++")

def pic():
    """Generate position independent code (for shared libraries)"""
    if _current_toolchain:
        _current_toolchain.cflags.append("-fPIC")
        _current_toolchain.cxxflags.append("-fPIC")

def pie():
    """Generate position independent executable"""
    if _current_toolchain:
        _current_toolchain.ldflags.append("-pie")
        _current_toolchain.cflags.append("-fPIE")
        _current_toolchain.cxxflags.append("-fPIE")

def sanitize(sanitizer: str):
    """Add sanitizer (address, thread, undefined, etc.)"""
    if _current_toolchain:
        flag = f"-fsanitize={sanitizer}"
        _current_toolchain.cflags.append(flag)
        _current_toolchain.cxxflags.append(flag)
        _current_toolchain.ldflags.append(flag)

def nowarnings():
    """Disable all warnings"""
    if _current_toolchain:
        _current_toolchain.cflags.append("-w")
        _current_toolchain.cxxflags.append("-w")

def profile(enable: bool = True):
    """Enable/disable profiling information"""
    if _current_toolchain:
        if enable:
            _current_toolchain.cflags.append("-pg")
            _current_toolchain.cxxflags.append("-pg")
            _current_toolchain.ldflags.append("-pg")

def coverage(enable: bool = True):
    """Enable/disable code coverage"""
    if _current_toolchain:
        if enable:
            _current_toolchain.cflags.append("--coverage")
            _current_toolchain.cxxflags.append("--coverage")
            _current_toolchain.ldflags.append("--coverage")

# ============================================================================
# PROJECT GROUPS
# ============================================================================

class group:
    """Project group context manager"""
    def __init__(self, name: str):
        self.name = name
        self.group_projects = []
        
    def __enter__(self):
        global _current_workspace
        if _current_workspace is None:
            raise RuntimeError("Group must be defined within a workspace")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Store group info in workspace
        if not hasattr(_current_workspace, 'groups'):
            _current_workspace.groups = {}
        _current_workspace.groups[self.name] = self.group_projects
        return False

# ============================================================================
# EXTERNAL PROJECT INCLUSION
# ============================================================================

def include(jenga_file: str, projects: list = None):
    """
    Include projects from external .jenga file
    
    Args:
        jenga_file: Path to .jenga file
        projects: Optional list of project names to include
                 - None: Include all projects
                 - ["ProjectA", "ProjectB"]: Include only these projects
    
    Examples:
        include("external/MyLib/mylib.jenga")  # Include all projects
        include("external/MyLib/mylib.jenga", ["Math", "Physics"])  # Include only Math and Physics
        include("libs/all.jenga", ["*"])  # Explicit: include all (same as None)
    """
    global _current_workspace
    
    if _current_workspace is None:
        raise RuntimeError("include() must be called within a workspace")
    
    from pathlib import Path
    
    jenga_path = Path(jenga_file)
    
    # Make relative to workspace location if not absolute
    if not jenga_path.is_absolute():
        workspace_dir = Path(_current_workspace.location) if _current_workspace.location else Path.cwd()
        jenga_path = workspace_dir / jenga_path
    
    if not jenga_path.exists():
        raise FileNotFoundError(f"External .jenga file not found: {jenga_path}")
    
    # Read and execute the external file
    with open(jenga_path, 'r', encoding='utf-8') as f:
        external_code = f.read()
    
    # Comment out imports
    import re
    external_code = re.sub(
        r'^(\s*)(from\s+jenga\..*?import\s+.*?)$',
        r'\1# \2  # Auto-commented by Jenga loader',
        external_code,
        flags=re.MULTILINE
    )
    
    # Execute in current context
    exec_globals = {
        '__file__': str(jenga_path.absolute()),
        '__name__': '__external__'
    }
    
    # Inject API
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import core.api as api
    exec_globals.update({
        name: getattr(api, name) 
        for name in dir(api) 
        if not name.startswith('_')
    })
    
    # Store current workspace state
    old_projects = dict(_current_workspace.projects)
    
    # Execute external file
    exec(external_code, exec_globals)
    
    # Projects added are now in workspace
    new_projects = set(_current_workspace.projects.keys()) - set(old_projects.keys())
    
    # Filter projects if specific list provided
    if projects is not None and "*" not in projects:
        # Remove projects not in the inclusion list
        for proj_name in list(new_projects):
            if proj_name not in projects:
                del _current_workspace.projects[proj_name]
                new_projects.remove(proj_name)
    
    # Mark included projects as external
    for proj_name in new_projects:
        if proj_name in _current_workspace.projects:
            _current_workspace.projects[proj_name]._external = True
            _current_workspace.projects[proj_name]._external_file = str(jenga_path)
    
    # Return list of included projects for user feedback
    return list(new_projects)


# ============================================================================
# CORE TOOLCHAIN FUNCTIONS
# ============================================================================

def sysroot(path: str):
    """Set system root directory"""
    if _current_toolchain:
        _current_toolchain.sysroot = path


def targettriple(triple: str):
    """Set target triple (e.g., 'x86_64-pc-linux-gnu')"""
    if _current_toolchain:
        _current_toolchain.targettriple = triple


def linker(linker_path: str):
    """Set linker path"""
    if _current_toolchain:
        _current_toolchain.linker = linker_path
        _current_toolchain.linker_path = linker_path


def archiver(archiver_path: str):
    """Set archiver path (e.g., 'ar' for static libraries)"""
    if _current_toolchain:
        _current_toolchain.archiver = archiver_path
        _current_toolchain.archiver_path = archiver_path


def flags(flag_type: str, flag_list: List[str]):
    """
    Set flags for specific type
    Example: flags("release", ["-O3", "-DNDEBUG"])
    """
    if _current_toolchain:
        if flag_type not in _current_toolchain.flags:
            _current_toolchain.flags[flag_type] = []
        _current_toolchain.flags[flag_type].extend(flag_list)


def cflags(flag_list: List[str]):
    """Set C-specific compiler flags"""
    if _current_toolchain:
        _current_toolchain.cflags.extend(flag_list)


def cxxflags(flag_list: List[str]):
    """Set C++-specific compiler flags"""
    if _current_toolchain:
        _current_toolchain.cxxflags.extend(flag_list)


def ldflags(flag_list: List[str]):
    """Set linker-specific flags"""
    if _current_toolchain:
        _current_toolchain.ldflags.extend(flag_list)


# ============================================================================
# BUILD OPTIONS
# ============================================================================

def buildoption(option: str, values: List[str]):
    """
    Set build option for current project
    Example: buildoption("auto_nomenclature", ["true"])
    """
    global _current_project
    
    if _current_project:
        if not hasattr(_current_project, 'buildoptions'):
            _current_project.buildoptions = {}
        
        if option not in _current_project.buildoptions:
            _current_project.buildoptions[option] = []
        
        _current_project.buildoptions[option].extend(values)


def buildoptions(options_dict: dict):
    """
    Set multiple build options at once
    Example: buildoptions({"auto_nomenclature": ["true"], "custom": ["value"]})
    """
    global _current_project
    
    if _current_project:
        if not hasattr(_current_project, 'buildoptions'):
            _current_project.buildoptions = {}
        
        for option, values in options_dict.items():
            if option not in _current_project.buildoptions:
                _current_project.buildoptions[option] = []
            
            if isinstance(values, list):
                _current_project.buildoptions[option].extend(values)
            else:
                _current_project.buildoptions[option].append(values)


# ============================================================================
# TOOLCHAIN UTILITY FUNCTIONS (for toolchain context)
# ============================================================================

def encoding(value: str = "utf-8"):
    """
    Set source and execution encoding for the current toolchain.
    Currently supports: utf-8
    
    This function automatically applies the correct compiler flags
    depending on the active compiler (MSVC, GCC, Clang).
    
    Example:
        encoding("utf-8")
    """
    if not _current_toolchain:
        return

    enc = value.lower()

    # Normalize
    if enc in ["utf8", "utf-8"]:
        compiler = _current_toolchain.compiler.lower()

        # MSVC
        if "msvc" in compiler or "cl" in compiler:
            _current_toolchain.cflags.append("/utf-8")
            _current_toolchain.cxxflags.append("/utf-8")

        # GCC / MinGW
        elif "gcc" in compiler or "g++" in compiler:
            _current_toolchain.cflags.extend([
                "-finput-charset=UTF-8",
                "-fexec-charset=UTF-8"
            ])
            _current_toolchain.cxxflags.extend([
                "-finput-charset=UTF-8",
                "-fexec-charset=UTF-8"
            ])

        # Clang
        elif "clang" in compiler:
            _current_toolchain.cflags.extend([
                "-finput-charset=UTF-8",
                "-fexec-charset=UTF-8"
            ])
            _current_toolchain.cxxflags.extend([
                "-finput-charset=UTF-8",
                "-fexec-charset=UTF-8"
            ])

        else:
            # Unknown compiler → best effort
            _current_toolchain.cflags.append("-finput-charset=UTF-8")
            _current_toolchain.cxxflags.append("-finput-charset=UTF-8")


def consoleencoding(compiler: str, encoding: str, *, cflags: list[str] | None = None, cxxflags: list[str] | None = None):
    if not _current_toolchain:
        return

    current = _current_toolchain.compiler.lower()
    target = compiler.lower()

    if target not in current:
        return  # Not the active compiler

    if cflags:
        _current_toolchain.cflags.extend(cflags)

    if cxxflags:
        _current_toolchain.cxxflags.extend(cxxflags)


def warnings_tc(warning_level: str):
    """Set warning level for toolchain"""
    if _current_toolchain:
        if warning_level.lower() == "all":
            _current_toolchain.cflags.append("-Wall")
            _current_toolchain.cxxflags.append("-Wall")
        elif warning_level.lower() == "extra":
            _current_toolchain.cflags.append("-Wextra")
            _current_toolchain.cxxflags.append("-Wextra")
        elif warning_level.lower() == "pedantic":
            _current_toolchain.cflags.append("-pedantic")
            _current_toolchain.cxxflags.append("-pedantic")
        elif warning_level.lower() == "everything":
            _current_toolchain.cxxflags.append("-Weverything")
        elif warning_level.lower() == "error":
            _current_toolchain.cflags.append("-Werror")
            _current_toolchain.cxxflags.append("-Werror")


def optimization_tc(level: str):
    """Set optimization level for toolchain"""
    if _current_toolchain:
        level = level.lower()
        if level in ["none", "0", "off"]:
            _current_toolchain.cflags.append("-O0")
            _current_toolchain.cxxflags.append("-O0")
        elif level in ["size", "s"]:
            _current_toolchain.cflags.append("-Os")
            _current_toolchain.cxxflags.append("-Os")
        elif level in ["fast", "1"]:
            _current_toolchain.cflags.append("-O1")
            _current_toolchain.cxxflags.append("-O1")
        elif level in ["balanced", "2"]:
            _current_toolchain.cflags.append("-O2")
            _current_toolchain.cxxflags.append("-O2")
        elif level in ["aggressive", "3", "full"]:
            _current_toolchain.cflags.append("-O3")
            _current_toolchain.cxxflags.append("-O3")
        elif level in ["fastest", "ofast"]:
            _current_toolchain.cflags.append("-Ofast")
            _current_toolchain.cxxflags.append("-Ofast")


def debug_tc(enable: bool = True):
    """Enable/disable debug information in toolchain"""
    if _current_toolchain:
        if enable:
            _current_toolchain.cflags.append("-g")
            _current_toolchain.cxxflags.append("-g")
        else:
            _current_toolchain.cflags.append("-g0")
            _current_toolchain.cxxflags.append("-g0")


# Aliases to work in toolchain context
def warnings(level: str):
    """Set warning level (works in both project and toolchain context)"""
    if _current_toolchain:
        warnings_tc(level)
    elif _current_project:
        _current_project.warnings = level


def optimization(level: str):
    """Set optimization level (works in both project and toolchain context)"""
    if _current_toolchain:
        optimization_tc(level)
    elif _current_project:
        _current_project.optimize = level


def debug(enable: bool = True):
    """Enable/disable debug info (works in both project and toolchain context)"""
    if _current_toolchain:
        debug_tc(enable)
    elif _current_project:
        _current_project.symbols = "On" if enable else "Off"