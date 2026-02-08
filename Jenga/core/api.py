#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Core API
Provides the DSL for configuring workspaces and projects
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from enum import Enum
import os
import sys
import re
import json


class ProjectKind(Enum):
    """Project types"""
    CONSOLE_APP = "ConsoleApp"
    WINDOWED_APP = "WindowedApp"
    STATIC_LIB = "StaticLib"
    SHARED_LIB = "SharedLib"
    TEST_SUITE = "TestSuite"
    # ANDROID_APP = "AndroidApp"
    # IOS_APP = "iOSApp"


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
    location: str = "."  # Now mandatory for projects
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
    
    # iOS specific
    iosbundleid: str = ""
    iosversion: str = "1.0"
    iosminsdk: str = "11.0"
    
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

    _in_workspace = True
    _standalone = True


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
        unitest_proj.targetdir = "%{wks.location}/Build/Lib/%{cfg.buildcfg}-%{cfg.system}"
        unitest_proj.objdir = "%{wks.location}/Build/Obj/%{cfg.buildcfg}-%{cfg.system}/__Unitest__"
        unitest_proj.targetname = "__Unitest__"
        
        # Add to workspace (hidden with __ prefix)
        self.workspace.projects["__Unitest__"] = unitest_proj
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_workspace
        # DON'T clear workspace - keep it available for commands
        return False
    

class project:
    """Project context manager"""
    def __init__(self, name: str):
        self.name = name
        self.project = None
        
    def __enter__(self):
        global _current_workspace, _current_project
        
        self.project = Project(name=self.name)
        
        if _current_workspace:
            # Si on est dans un workspace, ajouter au workspace
            self.project.location = "."  # Par défaut dans le workspace
            
            # MANDATORY: Set default toolchain if not specified
            if not self.project.toolchain and _current_workspace.toolchains:
                if 'default' in _current_workspace.toolchains:
                    self.project.toolchain = 'default'
                else:
                    self.project.toolchain = list(_current_workspace.toolchains.keys())[0]
            
            _current_workspace.projects[self.name] = self.project
            self.project._in_workspace = True
        else:
            # ✅ Projet standalone - ne pas lever d'erreur
            self.project._in_workspace = False
            self.project._standalone = True
            # Ne pas définir de location par défaut ici, le loader s'en chargera
        
        _current_project = self.project
        return self.project
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _current_project, _current_workspace
        
        # Only clear if we're in a workspace context
        if _current_workspace is not None:
            _current_project = None
        # else: keep _current_project for standalone detection
        
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
    def __init__(self, subname: str):
        self.subname = subname
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
        if self.parent_project and self.parent_project.location:
            self.project.location = self.parent_project.location
        else:
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
        
        # ========== AJOUTEZ CE BLOC ICI ==========
        # AUTOMATIC: Copy testfiles to files for compilation
        if self.project.testfiles:
            # Resolve test file patterns
            from pathlib import Path
            
            # Use parent project location as base
            base_dir = self.parent_project.location if self.parent_project else _current_workspace.location
            
            # Import resolve_file_list from variables module
            from .variables import resolve_file_list, VariableExpander
            
            # Create temporary expander
            expander = VariableExpander(_current_workspace, self.project, "Debug", "Windows")
            
            # Resolve patterns
            resolved_test_files = resolve_file_list(self.project.testfiles, base_dir, expander)
            
            # Add to project files
            self.project.files.extend(resolved_test_files)
            
            # Also copy parent's source files (excluding main)
            if self.parent_project and self.parent_project.files:
                parent_files = resolve_file_list(self.parent_project.files, 
                                                self.parent_project.location or _current_workspace.location,
                                                expander)
                
                # Filter out main file if specified
                if self.project.testmainfile:
                    main_file_resolved = expander.expand(self.project.testmainfile)
                    parent_files = [f for f in parent_files if f != main_file_resolved]
                
                self.project.files.extend(parent_files)
        
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


def androidapp():
    """Set project as Android application"""
    if _current_project:
        _current_project.kind = ProjectKind.WINDOWED_APP


def iosapp():
    """Set project as iOS application"""
    if _current_project:
        _current_project.kind = ProjectKind.WINDOWED_APP


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


def removefiles(file_list: List[str]):
    excludefiles(file_list)


def excludemainfiles(file_list: List[str]):
    """Exclude main files (for tests)"""
    if _current_project:
        _current_project.excludemainfiles.extend(file_list)


def removemainfiles(file_list: List[str]):
    excludemainfiles(file_list)


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
        if _current_filter and "system:" in _current_filter:
            system = _current_filter.split(":")[1]
            if system not in _current_project.system_links:
                _current_project.system_links[system] = []
            _current_project.system_links[system].extend(deps)
        else:
            _current_project.links.extend(deps)


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


# iOS settings
def iosbundleid(bundle_id: str):
    """Set iOS bundle ID"""
    if _current_project:
        _current_project.iosbundleid = bundle_id


def iosversion(version: str):
    """Set iOS version"""
    if _current_project:
        _current_project.iosversion = version


def iosminsdk(min_sdk: str):
    """Set iOS minimum SDK"""
    if _current_project:
        _current_project.iosminsdk = min_sdk


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
        for pattern in patterns:
            _current_project.files.append(pattern)


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


def linkerflags(flag_list: List[str]):
    """Set linker-specific flags"""
    ldflags(flag_list)


# ============================================================================
# EXTERNAL PROJECT INCLUSION
# ============================================================================

# def include(jenga_file: str, projects: list = None):
#     """
#     Include projects from external .jenga file
    
#     Args:
#         jenga_file: Path to .jenga file (relative to workspace or absolute)
#         projects: Optional list of project names to include
#                  - None: Include all projects
#                  - ["ProjectA", "ProjectB"]: Include only these projects
    
#     Supporte 3 formats:
#     1. Projets dans un workspace (standard):
#         with workspace("MyLib"): 
#             with project("Lib1"): ...
    
#     2. Projets standalone SANS workspace:
#         with project("Lib1"): ...  # Direct project definition
    
#     3. Mélange de projets et workspace:
#         with project("Lib1"): ...
#         with workspace("Other"): 
#             with project("Lib2"): ...
    
#     Les projets avec location="." sont relatifs au fichier .jenga externe.
#     """
#     global _current_workspace
    
#     if _current_workspace is None:
#         raise RuntimeError("include() must be called within a workspace")
    
#     from pathlib import Path
    
#     jenga_path = Path(jenga_file)
    
#     # Make relative to workspace location if not absolute
#     if not jenga_path.is_absolute():
#         workspace_dir = Path(_current_workspace.location) if _current_workspace.location else Path.cwd()
#         jenga_path = workspace_dir / jenga_path
    
#     if not jenga_path.exists():
#         raise FileNotFoundError(f"External .jenga file not found: {jenga_path}")
    
#     # Store the external file's directory for relative project locations
#     external_dir = jenga_path.parent.absolute()
    
#     # Save current state
#     old_projects = dict(_current_workspace.projects)
#     old_location = _current_workspace.location
#     old_toolchains = dict(_current_workspace.toolchains)
    
#     # Temporarily set workspace location to external directory
#     # This ensures that relative paths in external file are resolved correctly
#     original_location = _current_workspace.location
#     _current_workspace.location = str(external_dir)
    
#     # Read and execute the external file
#     with open(jenga_path, 'r', encoding='utf-8') as f:
#         external_code = f.read()
    
#     # Comment out imports
#     import re
#     external_code = re.sub(
#         r'^(\s*)(from\s+jenga\..*?import\s+.*?)$',
#         r'\1# \2  # Auto-commented by Jenga loader',
#         external_code,
#         flags=re.MULTILINE
#     )
    
#     # Create execution context
#     exec_globals = {
#         '__file__': str(jenga_path.absolute()),
#         '__name__': '__external__',
#         '_current_workspace': _current_workspace,
#         '_external_include': True,  # Flag to indicate we're in an include
#     }
    
#     # Inject ALL API functions
#     import sys
    
#     # Dynamically get all API functions
#     current_module = sys.modules[__name__]
#     for name in dir(current_module):
#         if not name.startswith('_'):
#             obj = getattr(current_module, name)
#             if callable(obj) or isinstance(obj, (int, float, str, list, dict, type)):
#                 exec_globals[name] = obj
    
#     # Also inject workspace class for standalone projects
#     exec_globals['Workspace'] = Workspace
    
#     # Store projects defined outside of workspace
#     standalone_projects = {}
#     original_projects_count = len(_current_workspace.projects)
    
#     try:
#         # Execute external file in its own directory
#         original_cwd = Path.cwd()
#         os.chdir(external_dir)
        
#         # Track if we're inside a workspace in the external file
#         external_workspace_active = False
        
#         # Helper function to track workspace context
#         class _TrackedWorkspace(workspace):
#             def __enter__(self):
#                 nonlocal external_workspace_active
#                 external_workspace_active = True
#                 return super().__enter__()
            
#             def __exit__(self, exc_type, exc_val, exc_tb):
#                 nonlocal external_workspace_active
#                 result = super().__exit__(exc_type, exc_val, exc_tb)
#                 external_workspace_active = False
#                 return result
        
#         exec_globals['workspace'] = _TrackedWorkspace
        
#         # Execute the code
#         exec(external_code, exec_globals)
        
#         # Check what was added
#         all_new_projects = set(_current_workspace.projects.keys()) - set(old_projects.keys())
        
#         # If no workspace was active during execution, projects were defined standalone
#         # They are already in _current_workspace.projects
#         if not external_workspace_active and all_new_projects:
#             # These are standalone projects
#             standalone_projects = {name: _current_workspace.projects[name] for name in all_new_projects}
        
#         # Filter projects if specific list provided
#         if projects is not None and "*" not in projects:
#             # Determine which projects to keep
#             projects_to_keep = set(projects)
            
#             # Remove projects not in the inclusion list
#             for proj_name in list(_current_workspace.projects.keys()):
#                 if proj_name in all_new_projects and proj_name not in projects_to_keep:
#                     del _current_workspace.projects[proj_name]
#                     if proj_name in standalone_projects:
#                         del standalone_projects[proj_name]
        
#         # Adjust project locations for included projects
#         for proj_name, proj in _current_workspace.projects.items():
#             if proj_name in all_new_projects:
#                 # Mark as external
#                 proj._external = True
#                 proj._external_file = str(jenga_path)
#                 proj._external_dir = str(external_dir)
#                 proj._standalone = proj_name in standalone_projects
                
#                 # Handle location: 
#                 # - If location is "." or empty, set to external directory
#                 # - If relative, make it relative to external directory (not main workspace)
#                 if proj.location == "." or not proj.location:
#                     # Means "same directory as the external .jenga file"
#                     proj.location = str(external_dir)
#                 elif not Path(proj.location).is_absolute():
#                     # Relative path - make it relative to external directory
#                     proj.location = str(external_dir / proj.location)
#                 # If absolute, leave as is
        
#         # Merge toolchains from external file
#         new_toolchains = set(_current_workspace.toolchains.keys()) - set(old_toolchains.keys())
#         for tc_name in new_toolchains:
#             # Mark as external toolchain
#             _current_toolchain = _current_workspace.toolchains[tc_name]
#             _current_toolchain._external = True
#             _current_toolchain._external_file = str(jenga_path)
        
#         # Restore workspace location
#         _current_workspace.location = original_location
        
#         # Restore original working directory
#         os.chdir(original_cwd)
        
#         # Return list of included projects for user feedback
#         included_projects = list(set(_current_workspace.projects.keys()) - set(old_projects.keys()))
#         return included_projects
        
#     except Exception as e:
#         # Restore on error
#         _current_workspace.location = original_location
        
#         # Restore original working directory
#         os.chdir(original_cwd)
        
#         raise RuntimeError(f"Error in included file {jenga_file}: {e}") from e


"""
NEW INCLUDE SYSTEM - Context Manager Based
Complete rewrite of the external project inclusion system
"""

# ============================================================================
# NOUVELLE APPROCHE: include comme context manager
# ============================================================================

class include:
    """
    Context manager for including external .jenga files
    
    Usage in workspace:
        with workspace("MyApp"):
            with toolchain("default", "g++"):
                # ... toolchain config
            
            # Include external projects
            with include("libs/logger/logger.jenga"):
                # Optionally filter which projects to include
                only(["Logger"])  # or skip(["Tests"])
            
            with include("libs/math/math.jenga"):
                # Include all projects from this file
                pass
            
            # Your own projects
            with project("MyApp"):
                # ... project config
                dependson(["Logger", "MathLib"])  # Reference included projects
    
    Features:
    - Clean context manager syntax
    - Automatic workspace isolation
    - Proper toolchain inheritance
    - Path resolution
    - Project filtering
    """
    
    def __init__(self, jenga_file: str):
        """
        Initialize include context
        
        Args:
            jenga_file: Path to external .jenga file (relative to workspace or absolute)
        """
        self.jenga_file = jenga_file
        self.jenga_path = None
        self.external_dir = None
        self.parent_workspace = None
        self.temp_workspace = None
        self.included_projects = []
        self.filter_mode = None  # 'only' or 'skip'
        self.filter_projects = []
        
    def __enter__(self):
        global _current_workspace, _current_project, _current_toolchain, _current_filter
        
        if _current_workspace is None:
            raise RuntimeError("include() must be used within a workspace context")
        
        from pathlib import Path
        import os
        
        # Save parent workspace
        self.parent_workspace = _current_workspace
        
        # Resolve path
        self.jenga_path = Path(self.jenga_file)
        if not self.jenga_path.is_absolute():
            workspace_dir = Path(self.parent_workspace.location) if self.parent_workspace.location else Path.cwd()
            self.jenga_path = workspace_dir / self.jenga_path
        
        if not self.jenga_path.exists():
            raise FileNotFoundError(f"External .jenga file not found: {self.jenga_path}")
        
        self.external_dir = self.jenga_path.parent.absolute()
        
        # Create isolated workspace for external file
        self.temp_workspace = Workspace(name=f"__include_{self.jenga_path.stem}__")
        self.temp_workspace.location = str(self.external_dir)
        
        # Copy toolchains from parent (inheritance)
        self.temp_workspace.toolchains = dict(self.parent_workspace.toolchains)
        
        # Read external file
        with open(self.jenga_path, 'r', encoding='utf-8') as f:
            external_code = f.read()
        
        # Comment out jenga imports
        import re
        external_code = re.sub(
            r'^(\s*)(from\s+[Jj]enga\..*?import\s+.*?)$',
            r'\1# \2  # Auto-commented by include',
            external_code,
            flags=re.MULTILINE
        )
        
        # Create execution context
        exec_globals = self._create_execution_context()
        
        # Save current directory
        self.original_cwd = Path.cwd()
        
        # Execute in external directory
        os.chdir(self.external_dir)
        
        try:
            # Switch to temp workspace
            _current_workspace = self.temp_workspace
            _current_project = None
            _current_toolchain = None
            _current_filter = None
            
            # Execute external file
            exec(external_code, exec_globals)
            
        finally:
            # Restore parent workspace
            _current_workspace = self.parent_workspace
            _current_project = None
            _current_toolchain = None
            _current_filter = None
            
            # Restore directory
            os.chdir(self.original_cwd)
        
        # Return self for filter methods (only/skip)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Transfer projects from temp workspace to parent workspace"""
        
        # Définir resolve_path UNE FOIS en dehors de la boucle
        def resolve_path(path, base_dir=None):
            """Resolve a path relative to external directory"""
            if base_dir is None:
                base_dir = self.external_dir
            
            from pathlib import Path
            path_obj = Path(path)
            
            # Si c'est déjà un chemin absolu, le garder
            if path_obj.is_absolute():
                return str(path_obj)
            
            # Si c'est un chemin avec des variables comme %{prj.location}, le garder tel quel
            if '%{' in path:
                return path
            
            # Faire le chemin relatif au dossier de base
            resolved = base_dir / path_obj
            
            # Essayer de le rendre relatif au workspace
            workspace_dir = Path(self.parent_workspace.location) if self.parent_workspace.location else Path.cwd()
            try:
                return str(resolved.relative_to(workspace_dir))
            except ValueError:
                # Si on ne peut pas le rendre relatif, garder le chemin absolu
                return str(resolved)
        
        # Déterminer quels projets inclure
        projects_to_include = set(self.temp_workspace.projects.keys())
        
        # Appliquer les filtres
        if self.filter_mode == 'only':
            projects_to_include &= set(self.filter_projects)
        elif self.filter_mode == 'skip':
            projects_to_include -= set(self.filter_projects)
        
        # Supprimer les projets cachés (comme __Unitest__)
        projects_to_include = {p for p in projects_to_include if not p.startswith('__')}
        
        # Transférer les projets
        from pathlib import Path
        
        for proj_name in projects_to_include:
            proj = self.temp_workspace.projects[proj_name]
            
            # Ajuster la localisation du projet
            if proj.location == "." or not proj.location:
                proj.location = str(self.external_dir)
            elif not Path(proj.location).is_absolute() and '%{' not in proj.location:
                proj.location = str(self.external_dir / Path(proj.location))
            
            # ============================================================
            # AJUSTER TOUS LES CHEMINS RELATIFS
            # ============================================================
            
            # 1. Chemins de fichiers et patterns
            adjusted_files = []
            for file_pattern in proj.files:
                # Si c'est un pattern glob ou contient des variables, le garder tel quel
                if '**' in file_pattern or '*' in file_pattern or '%{' in file_pattern:
                    adjusted_files.append(file_pattern)
                elif not Path(file_pattern).is_absolute():
                    adjusted_files.append(resolve_path(file_pattern))
                else:
                    adjusted_files.append(file_pattern)
            proj.files = adjusted_files
            
            # 2. Fichiers exclus
            adjusted_excludes = []
            for file_pattern in proj.excludefiles:
                if '**' in file_pattern or '*' in file_pattern or '%{' in file_pattern:
                    adjusted_excludes.append(file_pattern)
                elif not Path(file_pattern).is_absolute():
                    adjusted_excludes.append(resolve_path(file_pattern))
                else:
                    adjusted_excludes.append(file_pattern)
            proj.excludefiles = adjusted_excludes
            
            # 3. Fichiers main exclus (pour tests)
            adjusted_main_excludes = []
            for file_pattern in proj.excludemainfiles:
                if '**' in file_pattern or '*' in file_pattern or '%{' in file_pattern:
                    adjusted_main_excludes.append(file_pattern)
                elif not Path(file_pattern).is_absolute():
                    adjusted_main_excludes.append(resolve_path(file_pattern))
                else:
                    adjusted_main_excludes.append(file_pattern)
            proj.excludemainfiles = adjusted_main_excludes
            
            # 4. Répertoires d'inclusion
            proj.includedirs = [
                resolve_path(path) if not Path(path).is_absolute() and '%{' not in path else path 
                for path in proj.includedirs
            ]
            
            # 5. Répertoires de bibliothèques
            proj.libdirs = [
                resolve_path(path) if not Path(path).is_absolute() and '%{' not in path else path 
                for path in proj.libdirs
            ]
            
            # 6. Fichiers de dépendances (à copier)
            adjusted_dependfiles = []
            for pattern in proj.dependfiles:
                if '**' in pattern or '*' in pattern or '%{' in pattern:
                    adjusted_dependfiles.append(pattern)
                elif not Path(pattern).is_absolute():
                    adjusted_dependfiles.append(resolve_path(pattern))
                else:
                    adjusted_dependfiles.append(pattern)
            proj.dependfiles = adjusted_dependfiles
            
            # 7. Ressources embarquées
            adjusted_resources = []
            for resource in proj.embedresources:
                if not Path(resource).is_absolute():
                    adjusted_resources.append(resolve_path(resource))
                else:
                    adjusted_resources.append(resource)
            proj.embedresources = adjusted_resources
            
            # 8. Précompiled headers
            if proj.pchheader and not Path(proj.pchheader).is_absolute() and '%{' not in proj.pchheader:
                proj.pchheader = resolve_path(proj.pchheader)
            
            if proj.pchsource and not Path(proj.pchsource).is_absolute() and '%{' not in proj.pchsource:
                proj.pchsource = resolve_path(proj.pchsource)
            
            # 9. Test files
            adjusted_testfiles = []
            for pattern in proj.testfiles:
                if '**' in pattern or '*' in pattern or '%{' in pattern:
                    adjusted_testfiles.append(pattern)
                elif not Path(pattern).is_absolute():
                    adjusted_testfiles.append(resolve_path(pattern))
                else:
                    adjusted_testfiles.append(pattern)
            proj.testfiles = adjusted_testfiles
            
            # 10. Test main file
            if proj.testmainfile and not Path(proj.testmainfile).is_absolute() and '%{' not in proj.testmainfile:
                proj.testmainfile = resolve_path(proj.testmainfile)
            
            # 11. Test main template
            if proj.testmaintemplate and not Path(proj.testmaintemplate).is_absolute() and '%{' not in proj.testmaintemplate:
                proj.testmaintemplate = resolve_path(proj.testmaintemplate)
            
            # 12. Chemins Android (si définis)
            if hasattr(proj, 'androidkeystore') and proj.androidkeystore and not Path(proj.androidkeystore).is_absolute():
                proj.androidkeystore = resolve_path(proj.androidkeystore)
            
            # 13. Output directories (objdir, targetdir) - les garder avec les variables
            # Ces chemins utilisent généralement %{...} donc on ne les ajuste pas
            
            # ============================================================
            # MARQUER COMME EXTERNE
            # ============================================================
            proj._external = True
            proj._external_file = str(self.jenga_path)
            proj._external_dir = str(self.external_dir)
            proj._original_location = getattr(proj, '_original_location', proj.location)
            
            # ============================================================
            # AJOUTER AU WORKSPACE PARENT
            # ============================================================
            self.parent_workspace.projects[proj_name] = proj
            self.included_projects.append(proj_name)
        
        # Ajuster aussi les toolchains si nécessaire
        for tc_name, tc in self.temp_workspace.toolchains.items():
            if tc_name not in self.parent_workspace.toolchains:
                # Ajuster les chemins dans le toolchain
                if tc.sysroot and not Path(tc.sysroot).is_absolute():
                    tc.sysroot = str(self.external_dir / Path(tc.sysroot))
                
                if tc.toolchain_dir and not Path(tc.toolchain_dir).is_absolute():
                    tc.toolchain_dir = str(self.external_dir / Path(tc.toolchain_dir))
                
                # Marquer comme externe
                tc._external = True
                tc._external_file = str(self.jenga_path)
                
                # Ajouter au parent
                self.parent_workspace.toolchains[tc_name] = tc
        
        # Journaliser le succès
        # if self.included_projects:
        #     print(f"✅ Included {len(self.included_projects)} project(s) from {self.jenga_path.name}: {', '.join(self.included_projects)}")
        #     # Debug: montrer les chemins résolus
        #     for proj_name in self.included_projects:
        #         proj = self.parent_workspace.projects[proj_name]
        #         print(f"   {proj_name}:")
        #         print(f"     Location: {proj.location}")
        #         print(f"     Include dirs: {proj.includedirs}")
        #         print(f"     Files: {proj.files[:3]}{'...' if len(proj.files) > 3 else ''}")
        
        # Ajouter la détection des tests
        test_projects_found = []
        for proj_name in projects_to_include:
            proj = self.temp_workspace.projects[proj_name]
            if proj.is_test:
                test_projects_found.append({
                    'name': proj_name,
                    'parent': proj.parent_project,
                    'files': proj.testfiles
                })
        
                # 1. Vérifier si __Unitest__ existe dans le workspace parent
                if "__Unitest__" not in self.parent_workspace.projects:
                    print(f"  ⚠️  Attention: __Unitest__ non trouvé pour {proj_name}")
                else:
                    unitest_project = self.parent_workspace.projects["__Unitest__"]
                    proj.dependson.append("__Unitest__")
                    proj.includedirs.append(unitest_project.location + "/src")
                    proj.files.append(unitest_project.location + "/AutoMainTemplate/Entry.cpp")
        
        # if test_projects_found:
        #     print(f"📋 Tests détectés dans {self.jenga_path.name}:")
        #     for test in test_projects_found:
        #         print(f"  • {test['name']} (pour {test['parent']})")
        
        return False
    
    def get_test_projects(self):
        """Récupère les projets de test spécifiques à cet include"""
        test_projects = {}
        for name, proj in self.temp_workspace.projects.items():
            if proj.is_test:
                test_projects[name] = {
                    'parent': proj.parent_project,
                    'testfiles': proj.testfiles,
                    'location': proj.location
                }
        return test_projects
    
    def only(self, project_names: list):
        """
        Include only specified projects
        
        Usage:
            with include("lib.jenga") as inc:
                inc.only(["Logger", "Utils"])
        """
        self.filter_mode = 'only'
        self.filter_projects = project_names
        return self
    
    def skip(self, project_names: list):
        """
        Skip specified projects
        
        Usage:
            with include("lib.jenga") as inc:
                inc.skip(["Tests", "Examples"])
        """
        self.filter_mode = 'skip'
        self.filter_projects = project_names
        return self
    
    def _create_execution_context(self):
        """Create isolated execution context for external file"""
        import sys
        from pathlib import Path
        
        # Create clean namespace
        exec_globals = {
            '__file__': str(self.jenga_path),
            '__name__': '__external__',
            '__builtins__': __builtins__,
            'Path': Path,
            
            # CRITICAL: Inject state variables that will be used by exec()
            '_current_workspace': self.temp_workspace,
            '_current_project': None,
            '_current_toolchain': None,
            '_current_filter': None,
        }
        
        # Inject all API classes and functions
        current_module = sys.modules[__name__]
        
        exclude_items = {
            # Don't inject include itself to avoid recursion issues
            'include',
            'get_current_workspace',
            'reset_state',
        }
        
        for name in dir(current_module):
            if not name.startswith('_') and name not in exclude_items:
                obj = getattr(current_module, name)
                exec_globals[name] = obj
        
        return exec_globals
    
    # Dans la classe include, ajoutez:
    def getprojects(self) -> dict:
        """
        Get dictionary of included projects with their properties
        
        Returns:
            Dict mapping project names to their Project objects
            
        Example:
            with include("libs/logger/logger.jenga") as inc:
                projects = inc.get_projects()
                for name, proj in projects.items():
                    print(f"{name}: {proj.location}")
        """
        return self.temp_workspace.projects

    def getproject(self, name: str):
        """
        Get specific included project
        
        Args:
            name: Project name
            
        Returns:
            Project object or None if not found
            
        Example:
            with include("libs/logger/logger.jenga") as inc:
                logger = inc.get_project("Logger")
                if logger:
                    print(f"Logger include dirs: {logger.includedirs}")
        """
        return self.temp_workspace.projects.get(name)


# ============================================================================
# ALTERNATIVE SYNTAXES (for backward compatibility or preference)
# ============================================================================

def addprojects(jenga_file: str, projects: list = None):
    """
    Function-based alternative to include context manager
    For users who prefer function calls over context managers
    
    Usage:
        with workspace("MyApp"):
            # Include all projects
            includeprojects("libs/logger/logger.jenga")
            
            # Include specific projects
            includeprojects("libs/math/math.jenga", ["MathLib", "MathUtils"])
    """
    global _current_workspace
    
    if _current_workspace is None:
        raise RuntimeError("includeprojects() must be called within a workspace")
    
    # Use the include context manager internally
    with include(jenga_file) as inc:
        if projects:
            inc.only(projects)

    return inc.included_projects

def useproject(project_name: str, copy_includes: bool = True, copy_defines: bool = True):
    """
    Use properties from another project in current project
    
    Args:
        project_name: Name of project to use
        copy_includes: Whether to copy include directories
        copy_defines: Whether to copy preprocessor defines
    
    Example:
        with workspace("MyApp"):
            with include("libs/logger/logger.jenga"):
                pass
            
            with project("MyApp"):
                # Use Logger project properties
                useproject("Logger")
                # Now MyApp has Logger's include dirs and defines
                
                # Optional: copy only specific properties
                useproject("MathLib", copy_includes=True, copy_defines=False)
    """
    global _current_project, _current_workspace
    
    if not _current_project:
        raise RuntimeError("useproject() must be called within a project context")
    
    if project_name not in _current_workspace.projects:
        raise ValueError(f"Project '{project_name}' not found in workspace")
    
    source_project = _current_workspace.projects[project_name]
    
    # Copy properties as needed
    if copy_includes and source_project.includedirs:
        _current_project.includedirs.extend(source_project.includedirs)
    
    if copy_defines and source_project.defines:
        _current_project.defines.extend(source_project.defines)
    
    # Always add as dependency
    if project_name not in _current_project.dependson:
        _current_project.dependson.append(project_name)
    
    print(f"✅ Using properties from project '{project_name}'")


def getpp(project_name: str = None):
    """
    Get properties of a project (current or specified)
    
    Args:
        project_name: Name of project (None for current project)
    
    Returns:
        Dict with project properties including:
        - name, kind, language, location
        - files, includedirs, libdirs
        - defines, links, dependson
        - targetdir, targetname
        - is_test, parent_project (for tests)
        - external (if included from external file)
    
    Example:
        # Get current project properties
        props = get_project_properties()
        
        # Get specific project properties
        logger_props = get_project_properties("Logger")
        
        # Use in your project
        with project("MyApp"):
            logger_props = get_project_properties("Logger")
            includedirs(logger_props['includedirs'])
            links(logger_props['links'])
    """
    global _current_workspace, _current_project
    
    if not _current_workspace:
        return None
    
    if project_name is None:
        if _current_project:
            project = _current_project
        else:
            return None
    elif project_name in _current_workspace.projects:
        project = _current_workspace.projects[project_name]
    else:
        return None
    
    # Extract all relevant properties
    properties = {
        'name': project.name,
        'kind': project.kind.value,
        'language': project.language.value,
        'location': project.location,
        'cppdialect': project.cppdialect,
        'cdialect': project.cdialect,
        'files': list(project.files),
        'excludefiles': list(project.excludefiles),
        'includedirs': list(project.includedirs),
        'libdirs': list(project.libdirs),
        'objdir': project.objdir,
        'targetdir': project.targetdir,
        'targetname': project.targetname,
        'defines': list(project.defines),
        'optimize': project.optimize.value,
        'symbols': project.symbols,
        'warnings': project.warnings,
        'links': list(project.links),
        'dependson': list(project.dependson),
        'toolchain': project.toolchain,
        'is_test': getattr(project, 'is_test', False),
        'parent_project': getattr(project, 'parent_project', None),
    }
    
    # Add external project info if applicable
    if hasattr(project, '_external'):
        properties.update({
            'external': True,
            'external_file': getattr(project, '_external_file', 'unknown'),
            'external_dir': getattr(project, '_external_dir', 'unknown'),
        })
    
    return properties


# ============================================================================
# UTILITY FUNCTIONS FOR MANAGING INCLUDES
# ============================================================================

def listincludes() -> list:
    """
    List all included external projects in current workspace
    
    Returns:
        List of dicts with project info
    """
    global _current_workspace
    
    if not _current_workspace:
        return []
    
    includes = []
    for name, proj in _current_workspace.projects.items():
        if hasattr(proj, '_external') and proj._external:
            includes.append({
                'name': name,
                'source_file': proj._external_file,
                'source_dir': proj._external_dir,
                'location': proj.location,
            })
    
    return includes


def validateincludes():
    """
    Validate all included projects have valid dependencies
    Raises RuntimeError if issues found
    """
    global _current_workspace
    
    if not _current_workspace:
        return
    
    errors = []
    
    for proj_name, proj in _current_workspace.projects.items():
        # Check dependencies exist
        for dep in proj.dependson:
            if dep not in _current_workspace.projects:
                errors.append(
                    f"Project '{proj_name}' depends on '{dep}' which doesn't exist"
                )
    
    if errors:
        raise RuntimeError(
            "Dependency validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )
    
    print(f"✅ All {len(_current_workspace.projects)} projects validated successfully")


def getincludeinfo(project_name: str) -> dict:
    """
    Get detailed information about an included project
    
    Args:
        project_name: Name of the project
    
    Returns:
        Dict with project information or None if not found
    """
    global _current_workspace
    
    if not _current_workspace or project_name not in _current_workspace.projects:
        return None
    
    proj = _current_workspace.projects[project_name]
    
    info = {
        'name': proj.name,
        'kind': proj.kind.value,
        'language': proj.language.value,
        'location': proj.location,
        'is_external': hasattr(proj, '_external') and proj._external,
    }
    
    if info['is_external']:
        info.update({
            'source_file': proj._external_file,
            'source_dir': proj._external_dir,
        })
    
    return info



# ============================================================================
# ADVANCED FEATURES
# ============================================================================

class batch_include:
    """
    Include multiple .jenga files at once
    
    Usage:
        with batch_include([
            "libs/logger/logger.jenga",
            "libs/math/math.jenga",
            "libs/network/network.jenga"
        ]):
            # All projects from these files are included
            pass
        
        # Or with filters
        with batch_include({
            "libs/logger/logger.jenga": None,  # Include all
            "libs/math/math.jenga": ["MathLib"],  # Include only MathLib
            "libs/network/network.jenga": None,  # Include all
        }):
            pass
    """
    
    def __init__(self, includes):
        """
        Args:
            includes: List of paths or dict of {path: project_filter}
        """
        if isinstance(includes, list):
            self.includes = {path: None for path in includes}
        else:
            self.includes = includes
        
        self.included_projects = []
    
    def __enter__(self):
        for jenga_file, projects in self.includes.items():
            with include(jenga_file) as inc:
                if projects:
                    inc.only(projects)
            
            self.included_projects.extend(inc.included_projects)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.included_projects:
            print(f"✅ Batch included {len(self.included_projects)} total projects")
        return False


def include_from_directory(directory: str, pattern: str = "*.jenga"):
    """
    Include all .jenga files from a directory
    
    Usage:
        with workspace("MyApp"):
            # Include all .jenga files from libs/
            include_from_directory("libs")
            
            # Include only specific pattern
            include_from_directory("libs", "*_lib.jenga")
    """
    from pathlib import Path
    
    dir_path = Path(directory)
    if not dir_path.is_absolute():
        global _current_workspace
        if _current_workspace and _current_workspace.location:
            dir_path = Path(_current_workspace.location) / dir_path
    
    jenga_files = list(dir_path.glob(pattern))
    
    if not jenga_files:
        print(f"⚠️  No .jenga files found in {directory} matching {pattern}")
        return []
    
    included = []
    for jenga_file in jenga_files:
        with include(str(jenga_file)):
            pass
        included.append(str(jenga_file))
    
    print(f"✅ Included {len(included)} .jenga files from {directory}")
    return included


def create_include_execution_context(temp_workspace, external_dir, jenga_path):
    """Créer un contexte d'exécution SIMPLIFIÉ pour l'inclusion"""
    import sys
    from pathlib import Path
    
    # ⚠️ SOLUTION SIMPLE: Ne PAS créer de wrappers complexes
    # Juste injecter toutes les classes et fonctions API originales
    # Le _current_workspace sera mis à jour AVANT l'exec()
    
    exec_globals = {
        '__file__': str(jenga_path),
        '__name__': '__external__',
        '__builtins__': __builtins__,
        'Path': Path,
    }
    
    # ============================================================
    # INJECTION DE TOUTES LES CLASSES ET FONCTIONS API ORIGINALES
    # ============================================================
    current_module = sys.modules[__name__]
    
    # Liste complète à exclure
    exclude_items = {
        'include', 'create_include_execution_context',
        'lip', 'vip', 'get_current_workspace', 'reset_state',
    }
    
    # Injecter TOUTES les classes et fonctions (y compris project, workspace, etc.)
    for name in dir(current_module):
        if not name.startswith('_') and name not in exclude_items:
            obj = getattr(current_module, name)
            exec_globals[name] = obj
    
    return exec_globals


# ============================================================
# FONCTIONS UTILITAIRES SIMPLIFIÉES
# ============================================================

def lip():
    """List all included (external) projects"""
    if not _current_workspace:
        return []
    
    included = []
    for name, proj in _current_workspace.projects.items():
        if hasattr(proj, '_external') and proj._external:
            included.append({
                'name': name,
                'external_file': getattr(proj, '_external_file', 'unknown'),
                'location': proj.location,
                'standalone': getattr(proj, '_standalone', False)
            })
    return included


def vip():
    """Validate that all included projects have valid dependencies"""
    if not _current_workspace:
        return
    
    errors = []
    for name, proj in _current_workspace.projects.items():
        if hasattr(proj, '_external') and proj._external:
            for dep in proj.dependson:
                if dep not in _current_workspace.projects:
                    errors.append(f"Project '{name}' depends on '{dep}' which doesn't exist")
    
    if errors:
        raise RuntimeError(f"Dependency errors found:\n" + "\n".join(errors))
    

# ============================================================================
# UTILITY FUNCTIONS FOR INCLUDE SYSTEM
# ============================================================================

def getincludedprojects() -> Dict[str, Dict]:
    """
    Get information about all included (external) projects
    Useful for debugging and understanding dependency structure
    
    Returns: 
        Dict[str, Dict] where key is project name and value contains:
            - 'file': Path to the .jenga file
            - 'dir': Directory of the .jenga file
            - 'standalone': bool (True if project was defined without workspace)
            - 'location': Actual project location (after path resolution)
    
    Example usage in .jenga file:
        # Print included projects info
        included = get_included_projects()
        for name, info in included.items():
            print(f"{name}: from {info['file']}")
    """
    global _current_workspace
    
    if not _current_workspace:
        return {}
    
    included = {}
    for name, proj in _current_workspace.projects.items():
        if hasattr(proj, '_external') and proj._external:
            included[name] = {
                'file': getattr(proj, '_external_file', 'unknown'),
                'dir': getattr(proj, '_external_dir', 'unknown'),
                'standalone': getattr(proj, '_standalone', False),
                'location': proj.location,
                'original_location': getattr(proj, '_original_location', None),
            }
    
    return included


def getprojectinfo(project_name: str = None) -> Optional[Dict]:
    """
    Get detailed information about a specific project (or current project)
    
    Args:
        project_name: Name of project (None for current project)
    
    Returns:
        Dict with project information including source file, dependencies, etc.
    """
    global _current_workspace, _current_project
    
    if not _current_workspace:
        return None
    
    if project_name is None:
        if _current_project:
            project = _current_project
            project_name = project.name
        else:
            return None
    elif project_name in _current_workspace.projects:
        project = _current_workspace.projects[project_name]
    else:
        return None
    
    info = {
        'name': project.name,
        'kind': project.kind.value,
        'language': project.language.value,
        'location': project.location,
        'target_dir': project.targetdir,
        'target_name': project.targetname or project.name,
        'dependencies': list(project.dependson),
        'files': list(project.files),
        'include_dirs': list(project.includedirs),
        'is_test': getattr(project, 'is_test', False),
        'parent_project': getattr(project, 'parent_project', None),
    }
    
    # Add include information if external
    if hasattr(project, '_external'):
        info.update({
            'external': True,
            'external_file': getattr(project, '_external_file', 'unknown'),
            'external_dir': getattr(project, '_external_dir', 'unknown'),
            'standalone': getattr(project, '_standalone', False),
        })
    
    return info


def listallprojects() -> List[Dict]:
    """
    List all projects in the workspace with basic info
    
    Returns:
        List of project information dictionaries
    """
    global _current_workspace
    
    if not _current_workspace:
        return []
    
    projects = []
    for name, proj in _current_workspace.projects.items():
        projects.append({
            'name': name,
            'kind': proj.kind.value,
            'location': proj.location,
            'external': hasattr(proj, '_external'),
            'is_test': getattr(proj, 'is_test', False),
        })
    
    return projects


# Générer un rapport des dépendances
def generatedependencyreport():
    included = getincludedprojects()
    
    report = "# Jenga Dependency Report\n\n"
    report += "## External Libraries\n"
    
    for name, info in included.items():
        report += f"### {name}\n"
        report += f"- **Source**: `{info['file']}`\n"
        report += f"- **Location**: `{info['location']}`\n"
        report += f"- **Type**: {'Standalone' if info['standalone'] else 'Workspace'}\n\n"
    
    with open("DEPENDENCIES.md", "w") as f:
        f.write(report)


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


# ===========================================================================
# ANDROID ENHANCED API FUNCTIONS
# ===========================================================================

def androidabis(abis: List[str]):
    """
    Set Android ABIs to build
    
    Args:
        abis: List of ABIs (e.g., ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'])
    
    Examples:
        # Build for all ABIs
        androidabis(['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'])
        
        # Build only for ARM
        androidabis(['armeabi-v7a', 'arm64-v8a'])
        
        # Build only for 64-bit
        androidabis(['arm64-v8a', 'x86_64'])
    """
    if _current_project:
        _current_project.androidabis = abis


def androidproguard(enable: bool = True):
    """
    Enable ProGuard code obfuscation
    
    Args:
        enable: True to enable ProGuard
    
    Example:
        androidproguard(True)  # Enable for release builds
    """
    if _current_project:
        _current_project.androidproguard = enable


def androidproguardrules(rules: List[str]):
    """
    Add custom ProGuard rules
    
    Args:
        rules: List of ProGuard rule strings
    
    Example:
        androidproguardrules([
            "-keep class com.myapp.** { *; }",
            "-dontwarn javax.annotation.**"
        ])
    """
    if _current_project:
        if not hasattr(_current_project, 'androidproguardrules'):
            _current_project.androidproguardrules = []
        _current_project.androidproguardrules.extend(rules)


def androidassets(asset_patterns: List[str]):
    """
    Specify assets to include in APK/AAB
    
    Args:
        asset_patterns: List of file patterns (supports wildcards)
    
    Examples:
        # Single directory
        androidassets(["assets"])
        
        # Multiple patterns
        androidassets([
            "assets/**",
            "config/*.json",
            "data/textures/*"
        ])
    """
    if _current_project:
        if not hasattr(_current_project, 'androidassets'):
            _current_project.androidassets = []
        _current_project.androidassets.extend(asset_patterns)


def androidpermissions(permissions: List[str]):
    """
    Add Android permissions to manifest
    
    Args:
        permissions: List of permission names (can be short or full)
    
    Examples:
        # Short names (auto-prefixed with android.permission.)
        androidpermissions([
            "INTERNET",
            "WRITE_EXTERNAL_STORAGE",
            "CAMERA",
            "ACCESS_FINE_LOCATION"
        ])
        
        # Full names
        androidpermissions([
            "android.permission.INTERNET",
            "android.permission.CAMERA"
        ])
    """
    if _current_project:
        if not hasattr(_current_project, 'androidpermissions'):
            _current_project.androidpermissions = []
        _current_project.androidpermissions.extend(permissions)


def androidnativeactivity(enable: bool = True):
    """
    Use NativeActivity (pure C++) vs Java MainActivity
    
    Args:
        enable: True for NativeActivity, False for Java MainActivity
    
    Example:
        # Pure C++ app
        androidnativeactivity(True)
        
        # Java app with JNI
        androidnativeactivity(False)
    """
    if _current_project:
        _current_project.androidnativeactivity = enable


def androidcompilesdk(sdk: int):
    """
    Set Android compile SDK version
    
    Args:
        sdk: SDK version number
    
    Example:
        androidcompilesdk(33)  # Android 13
    """
    if _current_project:
        _current_project.androidcompilesdk = sdk


def ndkversion(version: str):
    """
    Set specific NDK version
    
    Args:
        version: NDK version string
    
    Example:
        ndkversion("25.1.8937393")
    """
    if _current_project:
        _current_project.ndkversion = version

@dataclass
class ToolConfig:
    """Configuration d'un outil externe"""
    name: str
    type: str  # 'compiler', 'sdk', 'ndk', 'emscripten', 'custom'
    version: str = ""
    path: str = ""
    
    # Compiler specific
    cc: str = ""
    cxx: str = ""
    ar: str = ""
    ld: str = ""
    strip: str = ""
    ranlib: str = ""
    
    # SDK specific
    sdk_path: str = ""
    include_paths: List[str] = field(default_factory=list)
    library_paths: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    
    # Environment variables
    env_vars: Dict[str, str] = field(default_factory=dict)
    
    # Tool flags
    cflags: List[str] = field(default_factory=list)
    cxxflags: List[str] = field(default_factory=list)
    ldflags: List[str] = field(default_factory=list)
    
    # System configuration
    sysroot: str = ""
    target_triple: str = ""
    
    # Validation
    validated: bool = False
    validation_error: str = ""
    
    def validate(self) -> bool:
        """Valider que l'outil existe et est fonctionnel"""
        import subprocess
        
        # Vérifier le chemin de base
        if self.path and not Path(self.path).exists():
            self.validation_error = f"Tool path not found: {self.path}"
            return False
        
        # Vérifier les exécutables
        for executable in [self.cc, self.cxx, self.ar, self.ld]:
            if executable:
                try:
                    # Vérifier si l'exécutable existe
                    result = subprocess.run(
                        [executable, '--version'] if not executable.endswith('.exe') else [executable],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode != 0:
                        self.validation_error = f"Tool not executable: {executable}"
                        return False
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    self.validation_error = f"Tool not found: {executable}"
                    return False
        
        self.validated = True
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour serialisation"""
        return {
            'name': self.name,
            'type': self.type,
            'version': self.version,
            'path': self.path,
            'cc': self.cc,
            'cxx': self.cxx,
            'ar': self.ar,
            'ld': self.ld,
            'strip': self.strip,
            'ranlib': self.ranlib,
            'sdk_path': self.sdk_path,
            'include_paths': self.include_paths,
            'library_paths': self.library_paths,
            'frameworks': self.frameworks,
            'env_vars': self.env_vars,
            'cflags': self.cflags,
            'cxxflags': self.cxxflags,
            'ldflags': self.ldflags,
            'sysroot': self.sysroot,
            'target_triple': self.target_triple,
            'validated': self.validated
        }


class ExternalToolsManager:
    """Gestionnaire d'outils externes"""
    
    def __init__(self):
        self.tools: Dict[str, ToolConfig] = {}
        self.active_tools: List[str] = []
        self.tools_cache_file = Path(".jenga") / "tools_cache.json"
        self._loaded = False
    
    def load_cache(self):
        """Charger le cache depuis le disque"""
        if not self._loaded and self.tools_cache_file.exists():
            try:
                with open(self.tools_cache_file, 'r') as f:
                    data = json.load(f)
                
                for tool_name, tool_data in data.get('tools', {}).items():
                    tool = ToolConfig(
                        name=tool_data['name'],
                        type=tool_data['type'],
                        version=tool_data['version'],
                        path=tool_data['path'],
                        cc=tool_data.get('cc', ''),
                        cxx=tool_data.get('cxx', ''),
                        ar=tool_data.get('ar', ''),
                        ld=tool_data.get('ld', ''),
                        strip=tool_data.get('strip', ''),
                        ranlib=tool_data.get('ranlib', ''),
                        sdk_path=tool_data.get('sdk_path', ''),
                        include_paths=tool_data.get('include_paths', []),
                        library_paths=tool_data.get('library_paths', []),
                        frameworks=tool_data.get('frameworks', []),
                        env_vars=tool_data.get('env_vars', {}),
                        cflags=tool_data.get('cflags', []),
                        cxxflags=tool_data.get('cxxflags', []),
                        ldflags=tool_data.get('ldflags', []),
                        sysroot=tool_data.get('sysroot', ''),
                        target_triple=tool_data.get('target_triple', ''),
                        validated=tool_data.get('validated', False)
                    )
                    self.tools[tool_name] = tool
                
                self.active_tools = data.get('active_tools', [])
                self._loaded = True
                
            except Exception as e:
                print(f"⚠️ Warning: Could not load tools cache: {e}")
    
    def save_cache(self):
        """Sauvegarder le cache sur le disque"""
        try:
            self.tools_cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'tools': {name: tool.to_dict() for name, tool in self.tools.items()},
                'active_tools': self.active_tools
            }
            
            with open(self.tools_cache_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ Warning: Could not save tools cache: {e}")
    
    def add_tool(self, tool: ToolConfig, activate: bool = True) -> bool:
        """Ajouter un outil au gestionnaire"""
        if tool.validate():
            self.tools[tool.name] = tool
            if activate and tool.name not in self.active_tools:
                self.active_tools.append(tool.name)
            self.save_cache()
            return True
        else:
            print(f"❌ Failed to add tool '{tool.name}': {tool.validation_error}")
            return False
    
    def get_tool(self, name: str) -> Optional[ToolConfig]:
        """Récupérer un outil par son nom"""
        self.load_cache()
        return self.tools.get(name)
    
    def get_active_tools(self) -> List[ToolConfig]:
        """Récupérer tous les outils actifs"""
        self.load_cache()
        return [self.tools[name] for name in self.active_tools if name in self.tools]
    
    def activate_tool(self, name: str) -> bool:
        """Activer un outil"""
        self.load_cache()
        if name in self.tools:
            if name not in self.active_tools:
                self.active_tools.append(name)
            self.save_cache()
            return True
        return False
    
    def deactivate_tool(self, name: str) -> bool:
        """Désactiver un outil"""
        self.load_cache()
        if name in self.active_tools:
            self.active_tools.remove(name)
            self.save_cache()
            return True
        return False
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Lister tous les outils"""
        self.load_cache()
        return [
            {
                'name': tool.name,
                'type': tool.type,
                'version': tool.version,
                'path': tool.path,
                'active': tool.name in self.active_tools,
                'validated': tool.validated
            }
            for tool in self.tools.values()
        ]


# Gestionnaire global
_tools_manager = ExternalToolsManager()


class addtools:
    """
    Context manager pour ajouter des outils externes au système de build
    
    Usage:
        # 1. Fichier local
        with workspace("MyProject"):
            with addtools("android-tools.jenga"):
                pass
        
        # 2. Outil intégré de Jenga
        with addtools("android-ndk"):  # Cherche dans Jenga/Tools/android-ndk.jenga
            pass
        
        # 3. Dict inline
        with addtools({
            "custom_gcc": {
                "type": "compiler",
                "path": "/opt/gcc-12"
            }
        }):
            pass
    """
    
    def __init__(self, tools_config, activate: bool = True):
        """
        Initialise le context manager
        
        Args:
            tools_config: Peut être:
                - Chemin vers fichier (.jenga, .json, .py)
                - Nom d'outil intégré (cherche dans Jenga/Tools/)
                - Dict de configuration inline
            activate: Si True, active automatiquement les outils
        """
        self.tools_config = tools_config
        self.activate = activate
        self.resolved_path = None
        self.loaded_tools = []
        self.previous_active_tools = []
    
    def __enter__(self):
        global _tools_manager
        
        # Sauvegarder l'état actuel
        self.previous_active_tools = _tools_manager.active_tools.copy()
        
        # Résoudre la configuration
        self._resolve_and_load_config()
        
        # Activer les outils si demandé
        if self.activate:
            for tool_name in self.loaded_tools:
                _tools_manager.activate_tool(tool_name)
        
        # Appliquer les variables d'environnement
        self._apply_environment_vars()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _tools_manager
        
        # Restaurer les variables d'environnement
        self._restore_environment_vars()
        
        # Restaurer l'état des outils actifs
        _tools_manager.active_tools = self.previous_active_tools
        _tools_manager.save_cache()
        
        return False
    
    def _resolve_and_load_config(self):
        """Résoudre et charger la configuration"""
        global _tools_manager
        
        # 1. Si c'est un dict, charger directement
        if isinstance(self.tools_config, dict):
            self._load_from_dict(self.tools_config)
            return
        
        # 2. Si c'est une chaîne, résoudre le chemin
        config_str = str(self.tools_config)
        
        # 2a. D'abord vérifier si c'est un outil intégré
        builtin_config = JengaToolsRegistry.load_builtin_tool_config(config_str)
        if builtin_config:
            self._load_from_dict(builtin_config)
            return
        
        # 2b. Résoudre le chemin
        self.resolved_path = self._resolve_tools_config(config_str)
        if not self.resolved_path:
            raise FileNotFoundError(
                f"Tools config not found: {config_str}\n"
                f"Searched in: current directory, workspace, Jenga/Tools/, ~/.jenga/tools/"
            )
        
        # 2c. Charger selon l'extension
        extension = self.resolved_path.suffix.lower()
        
        if extension == '.jenga':
            self._load_from_jenga_file()
        elif extension == '.json':
            self._load_from_json_file()
        elif extension == '.py':
            self._load_from_python_file()
        else:
            # Essayer de détecter automatiquement
            self._load_autodetect()
    
    def _resolve_tools_config(self, config_str: str) -> Optional[Path]:
        """Résoudre le chemin de configuration avec recherche hiérarchique"""
        from pathlib import Path
        
        # Liste des endroits où chercher
        search_locations = []
        
        # a. Chemin courant
        current = Path.cwd()
        search_locations.extend([
            current / config_str,
            current / f"{config_str}.jenga",
            current / f"{config_str}.json",
            current / f"{config_str}.py"
        ])
        
        # b. Workspace (si on en a un)
        workspace_path = self._find_workspace_path()
        if workspace_path:
            search_locations.extend([
                workspace_path / config_str,
                workspace_path / f"{config_str}.jenga",
                workspace_path / f"{config_str}.json",
                workspace_path / f"{config_str}.py",
                workspace_path / "tools" / config_str,
                workspace_path / "tools" / f"{config_str}.jenga"
            ])
        
        # c. Jenga/Tools/ (outils intégrés)
        jenga_tools_path = self._get_jenga_tools_path()
        if jenga_tools_path:
            search_locations.extend([
                jenga_tools_path / config_str,
                jenga_tools_path / f"{config_str}.jenga",
                jenga_tools_path / f"{config_str}.json",
                jenga_tools_path / f"{config_str}.py"
            ])
        
        # d. Environnement utilisateur
        user_tools_path = Path.home() / ".jenga" / "tools"
        if user_tools_path.exists():
            search_locations.extend([
                user_tools_path / config_str,
                user_tools_path / f"{config_str}.jenga",
                user_tools_path / f"{config_str}.json"
            ])
        
        # Chercher le premier qui existe
        for location in search_locations:
            if location.exists():
                return location
        
        return None
    
    def _get_jenga_tools_path(self) -> Optional[Path]:
        """Trouver le chemin de Jenga/Tools/"""
        import sys
        import os
        from pathlib import Path
        
        # Méthode 1: Chercher dans sys.path
        for sys_path in sys.path:
            if sys_path:
                tools_path = Path(sys_path) / "Jenga" / "Tools"
                if tools_path.exists():
                    return tools_path
        
        # Méthode 2: Chercher à côté du module
        try:
            import Jenga
            jenga_path = Path(Jenga.__file__).parent
            tools_path = jenga_path / "Tools"
            if tools_path.exists():
                return tools_path
        except:
            pass
        
        # Méthode 3: Chercher dans l'installation
        try:
            import site
            for site_packages in site.getsitepackages():
                tools_path = Path(site_packages) / "Jenga" / "Tools"
                if tools_path.exists():
                    return tools_path
        except:
            pass
        
        return None
    
    def _load_tools_config(self):
        """Charger la configuration d'outils depuis différents formats"""
        global _tools_manager
        
        from pathlib import Path
        
        # Si c'est déjà un dict
        if isinstance(self.tools_config, dict):
            self._load_from_dict(self.tools_config)
            return
        
        # Sinon, traiter comme un chemin
        config_path = Path(self.tools_config)
        
        # Si chemin relatif, essayer de le résoudre
        if not config_path.is_absolute():
            # Chercher dans le répertoire courant
            if config_path.exists():
                self.config_path = config_path
            else:
                # Chercher dans le workspace
                workspace_path = self._find_workspace_path()
                if workspace_path:
                    candidate = workspace_path / config_path
                    if candidate.exists():
                        self.config_path = candidate
                    else:
                        raise FileNotFoundError(f"Tools config not found: {config_path}")
                else:
                    raise FileNotFoundError(f"Tools config not found: {config_path}")
        else:
            self.config_path = config_path
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Tools config not found: {self.config_path}")
        
        # Charger selon l'extension
        extension = self.config_path.suffix.lower()
        
        if extension == '.jenga':
            self._load_from_jenga_file()
        elif extension == '.json':
            self._load_from_json_file()
        elif extension == '.py':
            self._load_from_python_file()
        else:
            raise ValueError(f"Unsupported tools config format: {extension}")
    
    def _load_from_jenga_file(self):
        """Charger depuis un fichier .jenga"""
        global _tools_manager
        
        try:
            # Lire le contenu du fichier
            content = self.config_path.read_text(encoding='utf-8')
            
            # Extraire les définitions d'outils
            # Format: tool_name = { ... }
            import re
            
            # Pattern pour trouver les définitions d'outils
            tool_pattern = r'(\w+)\s*=\s*(\{[^}]*\})'
            
            for match in re.finditer(tool_pattern, content, re.DOTALL):
                tool_name = match.group(1)
                tool_dict_str = match.group(2)
                
                try:
                    # Évaluer le dict (sécurisé)
                    tool_dict = self._safe_eval_dict(tool_dict_str)
                    tool_dict['name'] = tool_name
                    
                    # Créer et ajouter l'outil
                    tool = self._create_tool_from_dict(tool_dict)
                    if tool:
                        if _tools_manager.add_tool(tool, activate=self.activate):
                            self.loaded_tools.append(tool_name)
                            
                except Exception as e:
                    print(f"⚠️ Warning: Could not parse tool '{tool_name}': {e}")
        
        except Exception as e:
            raise RuntimeError(f"Failed to load tools from {self.config_path}: {e}")
    
    def _load_from_json_file(self):
        """Charger depuis un fichier JSON"""
        global _tools_manager
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                for tool_name, tool_dict in data.items():
                    if isinstance(tool_dict, dict):
                        tool_dict['name'] = tool_name
                        tool = self._create_tool_from_dict(tool_dict)
                        if tool:
                            if _tools_manager.add_tool(tool, activate=self.activate):
                                self.loaded_tools.append(tool_name)
        
        except Exception as e:
            raise RuntimeError(f"Failed to load tools from {self.config_path}: {e}")
    
    def _load_from_python_file(self):
        """Charger depuis un fichier Python"""
        global _tools_manager
        
        try:
            # Créer un contexte d'exécution sécurisé
            exec_globals = {
                '__file__': str(self.config_path),
                '__name__': '__tools_config__',
                'Path': Path,
            }
            
            # Exécuter le fichier
            exec(self.config_path.read_text(encoding='utf-8'), exec_globals)
            
            # Chercher les variables qui sont des dicts (outils)
            for var_name, var_value in exec_globals.items():
                if not var_name.startswith('_') and isinstance(var_value, dict):
                    if 'type' in var_value or 'path' in var_value:
                        var_value['name'] = var_name
                        tool = self._create_tool_from_dict(var_value)
                        if tool:
                            if _tools_manager.add_tool(tool, activate=self.activate):
                                self.loaded_tools.append(var_name)
        
        except Exception as e:
            raise RuntimeError(f"Failed to load tools from {self.config_path}: {e}")
    
    def _load_from_dict(self, config_dict: dict):
        """Charger depuis un dict inline"""
        global _tools_manager
        
        for tool_name, tool_dict in config_dict.items():
            if isinstance(tool_dict, dict):
                tool_dict['name'] = tool_name
                tool = self._create_tool_from_dict(tool_dict)
                if tool:
                    if _tools_manager.add_tool(tool, activate=self.activate):
                        self.loaded_tools.append(tool_name)
    
    def _create_tool_from_dict(self, tool_dict: dict) -> Optional[ToolConfig]:
        """Créer un ToolConfig depuis un dict"""
        
        # Déterminer le type d'outil
        tool_type = tool_dict.get('type', 'custom')
        
        # Remplacer les variables {path} par le chemin réel
        path = tool_dict.get('path', '')
        if path and '{' in path:
            # Pour l'instant, on ne fait pas de remplacement complexe
            pass
        
        # Créer la configuration
        tool = ToolConfig(
            name=tool_dict['name'],
            type=tool_type,
            version=tool_dict.get('version', ''),
            path=tool_dict.get('path', ''),
            cc=tool_dict.get('cc', ''),
            cxx=tool_dict.get('cxx', ''),
            ar=tool_dict.get('ar', ''),
            ld=tool_dict.get('ld', ''),
            strip=tool_dict.get('strip', ''),
            ranlib=tool_dict.get('ranlib', ''),
            sdk_path=tool_dict.get('sdk_path', ''),
            include_paths=tool_dict.get('include_paths', []),
            library_paths=tool_dict.get('library_paths', []),
            frameworks=tool_dict.get('frameworks', []),
            env_vars=tool_dict.get('env_vars', {}),
            cflags=tool_dict.get('cflags', []),
            cxxflags=tool_dict.get('cxxflags', []),
            ldflags=tool_dict.get('ldflags', []),
            sysroot=tool_dict.get('sysroot', ''),
            target_triple=tool_dict.get('target_triple', '')
        )
        
        return tool
    
    def _safe_eval_dict(self, dict_str: str) -> dict:
        """Évaluer un dict de manière sécurisée"""
        # Remplacer les références de chemin
        dict_str = dict_str.replace('{path}', str(self.config_path.parent) if self.config_path else '')
        
        # Utiliser ast.literal_eval pour la sécurité
        import ast
        try:
            return ast.literal_eval(dict_str)
        except:
            # Fallback: évaluation simple pour les dicts basiques
            dict_str = dict_str.strip()
            if dict_str.startswith('{') and dict_str.endswith('}'):
                # Extraction manuelle
                import re
                result = {}
                pairs = re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', dict_str)
                for key, value in pairs:
                    result[key] = value
                return result
        
        return {}
    
    def _find_workspace_path(self) -> Optional[Path]:
        """Trouver le chemin du workspace courant"""
        from pathlib import Path
        
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if any(parent.glob("*.jenga")):
                return parent
        
        return None
    
    def _apply_environment_vars(self):
        """Appliquer les variables d'environnement des outils actifs"""
        global _tools_manager
        
        self.original_env = {}
        
        for tool in _tools_manager.get_active_tools():
            for env_var, value in tool.env_vars.items():
                # Sauvegarder la valeur originale
                if env_var in os.environ:
                    self.original_env[env_var] = os.environ[env_var]
                
                # Appliquer la nouvelle valeur
                os.environ[env_var] = value
    
    def _restore_environment_vars(self):
        """Restaurer les variables d'environnement originales"""
        for env_var, value in self.original_env.items():
            os.environ[env_var] = value
    
    def get_tool_config(self, name: str) -> Optional[ToolConfig]:
        """Récupérer la configuration d'un outil spécifique"""
        global _tools_manager
        return _tools_manager.get_tool(name)
    
    def list_loaded_tools(self) -> List[str]:
        """Lister les outils chargés dans ce contexte"""
        return self.loaded_tools.copy()
    
    def activate_tool(self, name: str) -> bool:
        """Activer un outil spécifique"""
        global _tools_manager
        return _tools_manager.activate_tool(name)
    
    def deactivate_tool(self, name: str) -> bool:
        """Désactiver un outil spécifique"""
        global _tools_manager
        return _tools_manager.deactivate_tool(name)


# ============================================================================
# FUNCTIONS POUR UTILISATION DIRECTE DANS .jenga FILES
# ============================================================================

def addexternaltools(tools_config: str, activate: bool = True):
    """
    Fonction pour ajouter des outils externes (compatibilité avec context manager)
    
    Usage:
        addexternaltools("android-tools.jenga")
        addexternaltools({
            "custom_gcc": {
                "type": "compiler",
                "path": "/opt/gcc-12",
                "cc": "/opt/gcc-12/bin/gcc"
            }
        })
    """
    global _tools_manager
    
    # Créer un contexte temporaire
    with addtools(tools_config, activate):
        pass


def usetool(tool_name: str):
    """
    Utiliser un outil spécifique pour le projet courant
    
    Usage:
        with project("MyApp"):
            usetool("android-ndk-r25")
    """
    global _current_project, _tools_manager
    
    if not _current_project:
        raise RuntimeError("usetool() must be called within a project context")
    
    tool = _tools_manager.get_tool(tool_name)
    if not tool:
        raise ValueError(f"Tool not found: {tool_name}")
    
    # Activer l'outil
    _tools_manager.activate_tool(tool_name)
    
    # Configurer le projet pour utiliser cet outil
    _current_project.toolchain = f"tool_{tool_name}"
    
    print(f"✅ Using tool: {tool_name}")


def listtools() -> List[Dict[str, Any]]:
    """Lister tous les outils disponibles"""
    global _tools_manager
    return _tools_manager.list_tools()


def gettoolinfo(tool_name: str) -> Optional[Dict[str, Any]]:
    """Obtenir des informations détaillées sur un outil"""
    global _tools_manager
    
    tool = _tools_manager.get_tool(tool_name)
    if not tool:
        return None
    
    info = tool.to_dict()
    info['active'] = tool_name in _tools_manager.active_tools
    
    return info


def validatetools() -> List[Dict[str, Any]]:
    """Valider tous les outils actifs"""
    global _tools_manager
    
    results = []
    for tool_name in _tools_manager.active_tools:
        tool = _tools_manager.get_tool(tool_name)
        if tool:
            is_valid = tool.validate()
            results.append({
                'name': tool_name,
                'valid': is_valid,
                'error': tool.validation_error if not is_valid else '',
                'type': tool.type
            })
    
    return results


class JengaToolsRegistry:
    """Registre des outils intégrés de Jenga"""
    
    BUILTIN_TOOLS = {
        # Android NDK
        "android-ndk": {
            "name": "android-ndk",
            "type": "ndk",
            "description": "Android Native Development Kit",
            "config_template": "android_ndk.jenga",
            "detect_function": "detect_android_ndk"
        },
        
        # Emscripten
        "emscripten": {
            "name": "emscripten", 
            "type": "emscripten",
            "description": "Emscripten SDK for WebAssembly",
            "config_template": "emscripten.jenga",
            "detect_function": "detect_emscripten"
        },
        
        # Visual Studio
        "msvc": {
            "name": "msvc",
            "type": "compiler",
            "description": "Microsoft Visual C++ Compiler",
            "config_template": "msvc.jenga",
            "detect_function": "detect_msvc"
        },
        
        # Xcode
        "xcode": {
            "name": "xcode",
            "type": "sdk",
            "description": "Xcode SDK for macOS/iOS",
            "config_template": "xcode.jenga",
            "detect_function": "detect_xcode"
        }
    }
    
    @classmethod
    def get_builtin_tool(cls, tool_name: str) -> Optional[Dict]:
        """Récupérer un outil intégré par son nom"""
        return cls.BUILTIN_TOOLS.get(tool_name)
    
    @classmethod
    def list_builtin_tools(cls) -> List[Dict]:
        """Lister tous les outils intégrés"""
        return [
            {
                'name': tool['name'],
                'type': tool['type'],
                'description': tool['description']
            }
            for tool in cls.BUILTIN_TOOLS.values()
        ]
    
    @classmethod
    def load_builtin_tool_config(cls, tool_name: str) -> Optional[Dict]:
        """Charger la configuration d'un outil intégré"""
        import importlib.resources
        
        try:
            # Essayer de charger depuis Jenga/Tools/
            from Jenga import Tools
            
            # Construire le nom du module
            module_name = f"Jenga.Tools.{tool_name}"
            
            try:
                module = importlib.import_module(module_name)
                
                # Appeler la fonction de configuration
                if hasattr(module, 'get_config'):
                    return module.get_config()
                
                # Sinon, chercher un dict appelé CONFIG
                if hasattr(module, 'CONFIG'):
                    return getattr(module, 'CONFIG')
                    
            except ImportError:
                # Essayer de charger depuis un fichier
                tools_path = cls._get_tools_path()
                config_files = [
                    tools_path / f"{tool_name}.jenga",
                    tools_path / f"{tool_name}.json",
                    tools_path / f"{tool_name}.py"
                ]
                
                for config_file in config_files:
                    if config_file.exists():
                        # Charger selon le type
                        if config_file.suffix == '.jenga':
                            return cls._load_jenga_config(config_file)
                        elif config_file.suffix == '.json':
                            return cls._load_json_config(config_file)
                        elif config_file.suffix == '.py':
                            return cls._load_python_config(config_file)
                
        except Exception as e:
            print(f"⚠️ Warning: Could not load builtin tool '{tool_name}': {e}")
        
        return None
    
    @staticmethod
    def _get_tools_path() -> Path:
        """Trouver le chemin de Jenga/Tools/"""
        import sys
        from pathlib import Path
        
        # Chercher dans sys.path
        for path in sys.path:
            tools_path = Path(path) / "Jenga" / "Tools"
            if tools_path.exists():
                return tools_path
        
        # Chercher à côté du module
        try:
            import Jenga
            jenga_path = Path(Jenga.__file__).parent
            return jenga_path / "Tools"
        except:
            pass
        
        return None

# ============================================================================
# PRE-CONFIGURED TOOL TEMPLATES
# ============================================================================

def create_android_ndk_tool(ndk_path: str, api_level: int = 21, arch: str = "arm64-v8a"):
    """
    Créer un outil Android NDK pré-configuré
    
    Args:
        ndk_path: Chemin vers Android NDK
        api_level: Niveau API Android
        arch: Architecture cible (arm64-v8a, armeabi-v7a, x86, x86_64)
    """
    
    ndk_path = Path(ndk_path).absolute()
    
    # Déterminer le triple cible
    triples = {
        "arm64-v8a": f"aarch64-linux-android{api_level}",
        "armeabi-v7a": f"armv7a-linux-androideabi{api_level}",
        "x86": f"i686-linux-android{api_level}",
        "x86_64": f"x86_64-linux-android{api_level}"
    }
    
    target_triple = triples.get(arch, f"aarch64-linux-android{api_level}")
    
    # Trouver les chemins des outils
    toolchain_dir = None
    for potential in ndk_path.glob("toolchains/llvm/prebuilt/*"):
        if potential.is_dir():
            toolchain_dir = potential
            break
    
    if not toolchain_dir:
        raise FileNotFoundError(f"Could not find LLVM toolchain in {ndk_path}")
    
    tool_config = {
        "name": f"android-ndk-api{api_level}-{arch}",
        "type": "ndk",
        "path": str(ndk_path),
        "version": "r25",  # À détecter automatiquement si possible
        "cc": str(toolchain_dir / "bin" / f"{target_triple}-clang"),
        "cxx": str(toolchain_dir / "bin" / f"{target_triple}-clang++"),
        "ar": str(toolchain_dir / "bin" / "llvm-ar"),
        "ld": str(toolchain_dir / "bin" / "ld"),
        "strip": str(toolchain_dir / "bin" / "llvm-strip"),
        "ranlib": str(toolchain_dir / "bin" / "llvm-ranlib"),
        "sysroot": str(toolchain_dir / "sysroot"),
        "target_triple": target_triple,
        "cflags": [
            f"-DANDROID",
            f"-D__ANDROID_API__={api_level}",
            "-fPIC",
            "-fno-exceptions",
            "-fno-rtti"
        ],
        "cxxflags": [
            "-std=c++17",
            "-frtti",
            "-fexceptions"
        ],
        "ldflags": [
            "-llog",
            "-landroid",
            "-lEGL",
            "-lGLESv3"
        ],
        "env_vars": {
            "ANDROID_NDK_ROOT": str(ndk_path),
            "ANDROID_NDK_HOME": str(ndk_path),
            "ANDROID_API": str(api_level)
        }
    }
    
    return tool_config


def create_emscripten_tool(emsdk_path: str):
    """
    Créer un outil Emscripten pré-configuré
    
    Args:
        emsdk_path: Chemin vers Emscripten SDK
    """
    
    emsdk_path = Path(emsdk_path).absolute()
    
    # Trouver emcc
    emcc_path = None
    for potential in [
        emsdk_path / "emcc",
        emsdk_path / "emsdk" / "emcc",
        emsdk_path / "upstream" / "emscripten" / "emcc"
    ]:
        if potential.exists():
            emcc_path = potential.parent
            break
    
    if not emcc_path:
        # Chercher dans le PATH
        import shutil
        emcc_path = shutil.which("emcc")
        if emcc_path:
            emcc_path = Path(emcc_path).parent
    
    if not emcc_path:
        raise FileNotFoundError(f"Could not find emcc in {emsdk_path}")
    
    tool_config = {
        "name": "emscripten",
        "type": "emscripten",
        "path": str(emsdk_path),
        "cc": str(emcc_path / "emcc"),
        "cxx": str(emcc_path / "em++"),
        "ar": str(emcc_path / "emar"),
        "cflags": [
            "-D__EMSCRIPTEN__",
            "-s WASM=1",
            "-s USE_WEBGL2=1",
            "-s USE_SDL=2"
        ],
        "cxxflags": [
            "-std=c++17",
            "-s USE_PTHREADS=1"
        ],
        "ldflags": [
            "-s ALLOW_MEMORY_GROWTH=1",
            "-s EXPORTED_FUNCTIONS='[\"_main\"]'",
            "-s EXPORTED_RUNTIME_METHODS='[\"ccall\",\"cwrap\"]'"
        ],
        "env_vars": {
            "EMSDK": str(emsdk_path),
            "EMSCRIPTEN": str(emsdk_path / "upstream" / "emscripten")
        }
    }
    
    return tool_config


def create_custom_gcc_tool(gcc_path: str, version: str = ""):
    """
    Créer un outil GCC personnalisé
    
    Args:
        gcc_path: Chemin vers l'installation GCC
        version: Version de GCC (ex: "12.2.0")
    """
    
    gcc_path = Path(gcc_path).absolute()
    
    tool_config = {
        "name": f"gcc-custom-{version}" if version else "gcc-custom",
        "type": "compiler",
        "path": str(gcc_path),
        "version": version,
        "cc": str(gcc_path / "bin" / "gcc"),
        "cxx": str(gcc_path / "bin" / "g++"),
        "ar": str(gcc_path / "bin" / "ar"),
        "ld": str(gcc_path / "bin" / "ld"),
        "strip": str(gcc_path / "bin" / "strip"),
        "ranlib": str(gcc_path / "bin" / "ranlib"),
        "cflags": [
            "-march=native",
            "-mtune=native",
            "-O3",
            "-pipe"
        ],
        "cxxflags": [
            "-std=c++20",
            "-fcoroutines"
        ],
        "env_vars": {
            "CUSTOM_GCC_ROOT": str(gcc_path)
        }
    }
    
    return tool_config


# ============================================================================
# INTEGRATION WITH JENGA API
# ============================================================================

def get_current_toolchain_config() -> Optional[Dict[str, Any]]:
    """
    Obtenir la configuration de l'outil actuel pour le projet courant
    
    Returns:
        Dict avec la configuration de l'outil ou None
    """
    global _current_project, _tools_manager
    
    if not _current_project or not _current_project.toolchain:
        return None
    
    toolchain_name = _current_project.toolchain
    
    # Vérifier si c'est un outil personnalisé (préfixe tool_)
    if toolchain_name.startswith("tool_"):
        tool_name = toolchain_name[5:]  # Enlever "tool_"
        tool = _tools_manager.get_tool(tool_name)
        if tool:
            return tool.to_dict()
    
    return None


def inject_tool_flags_into_toolchain():
    """
    Injecter les flags des outils actifs dans le toolchain courant
    
    Cette fonction est appelée automatiquement par le système de build
    """
    global _current_toolchain, _tools_manager
    
    if not _current_toolchain:
        return
    
    # Pour chaque outil actif, injecter ses flags
    for tool in _tools_manager.get_active_tools():
        # Injecter les flags C
        if tool.cflags:
            _current_toolchain.cflags.extend(tool.cflags)
        
        # Injecter les flags C++
        if tool.cxxflags:
            _current_toolchain.cxxflags.extend(tool.cxxflags)
        
        # Injecter les flags linker
        if tool.ldflags:
            _current_toolchain.ldflags.extend(tool.ldflags)
        
        # Configurer les chemins des compilateurs si spécifiés
        if tool.cc and not _current_toolchain.ccompiler:
            _current_toolchain.ccompiler = tool.cc
            _current_toolchain.ccompiler_path = tool.cc
        
        if tool.cxx and not _current_toolchain.cppcompiler:
            _current_toolchain.cppcompiler = tool.cxx
            _current_toolchain.cppcompiler_path = tool.cxx
        
        if tool.ar and not _current_toolchain.archiver:
            _current_toolchain.archiver = tool.ar
            _current_toolchain.archiver_path = tool.ar
        
        if tool.ld and not _current_toolchain.linker:
            _current_toolchain.linker = tool.ld
            _current_toolchain.linker_path = tool.ld
        
        # Configurer sysroot
        if tool.sysroot and not _current_toolchain.sysroot:
            _current_toolchain.sysroot = tool.sysroot


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_tools_system():
    """Initialiser le système d'outils (appelé au démarrage de Jenga)"""
    global _tools_manager
    
    # Charger le cache
    _tools_manager.load_cache()
    
    # Appliquer les variables d'environnement des outils actifs
    for tool in _tools_manager.get_active_tools():
        for env_var, value in tool.env_vars.items():
            os.environ[env_var] = value
    
    print(f"✅ Tools system initialized with {len(_tools_manager.active_tools)} active tools")


# Exporter les fonctions principales
__all__ = [
    'addtools',
    'usetool',
    'listtools',
    'gettoolinfo',
    'validatetools',
    'create_android_ndk_tool',
    'create_emscripten_tool',
    'create_custom_gcc_tool',
    'get_current_toolchain_config',
    'inject_tool_flags_into_toolchain',
    'init_tools_system'
]


# ===========================================================================
# EXAMPLE USAGE IN .jenga FILE
# ===========================================================================

"""
Example .jenga file with all Android features:

with workspace("MyAndroidGame"):
    configurations(["Debug", "Release"])
    platforms(["Android"])
    
    # Android SDK/NDK configuration
    androidsdkpath("/path/to/android-sdk")
    androidndkpath("/path/to/android-ndk")
    javajdkpath("/path/to/jdk")  # Optional
    
    with project("Game"):
        androidapp()
        language("C++")
        cppdialect("C++17")
        
        files(["src/**.cpp"])
        includedirs(["include"])
        
        # Basic Android config
        androidapplicationid("com.mygame.android")
        androidversioncode(1)
        androidversionname("1.0.0")
        androidminsdk(21)
        androidtargetsdk(33)
        androidcompilesdk(33)
        
        # ✨ NEW: Multi-ABI support
        androidabis([
            "armeabi-v7a",  # 32-bit ARM
            "arm64-v8a",    # 64-bit ARM (required for Play Store)
            "x86",          # 32-bit x86 (emulator)
            "x86_64"        # 64-bit x86 (emulator)
        ])
        
        # Or just ARM for smaller APK
        # androidabis(["armeabi-v7a", "arm64-v8a"])
        
        # ✨ NEW: ProGuard obfuscation
        androidproguard(True)  # Enable for Release
        androidproguardrules([
            "-keep class com.mygame.** { *; }",
            "-dontwarn org.lwjgl.**",
            "-keepattributes *Annotation*"
        ])
        
        # ✨ NEW: Assets management
        androidassets([
            "assets",           # Copy entire assets directory
            "config/*.json",    # Copy all JSON configs
            "data/textures/*"   # Copy textures
        ])
        
        # ✨ NEW: Permissions
        androidpermissions([
            "INTERNET",
            "WRITE_EXTERNAL_STORAGE",
            "READ_EXTERNAL_STORAGE",
            "CAMERA",
            "ACCESS_FINE_LOCATION",
            "ACCESS_COARSE_LOCATION"
        ])
        
        # Native activity (pure C++) or Java activity
        androidnativeactivity(True)  # True = NativeActivity, False = MainActivity
        
        # NDK version
        ndkversion("25.1.8937393")
        
        # Signing (optional)
        androidsign(True)
        androidkeystore("mygame.keystore")
        androidkeystorepass("mypassword")
        androidkeyalias("key0")
        
        targetdir("Build/Android/%{cfg.buildcfg}")


# Building:
# jenga build --platform Android --config Release
# jenga package --platform Android --type apk     # APK for testing
# jenga package --platform Android --type aab     # AAB for Play Store
"""

# ===========================================================================
# COMMON ANDROID PERMISSIONS REFERENCE
# ===========================================================================

ANDROID_PERMISSIONS_REFERENCE = """
Common Android Permissions:

# Network
INTERNET                      - Access internet
ACCESS_NETWORK_STATE          - Check network status
ACCESS_WIFI_STATE             - Access WiFi state

# Storage
WRITE_EXTERNAL_STORAGE        - Write to external storage
READ_EXTERNAL_STORAGE         - Read from external storage
MANAGE_EXTERNAL_STORAGE       - Manage all files (Android 11+)

# Location
ACCESS_FINE_LOCATION          - Precise location
ACCESS_COARSE_LOCATION        - Approximate location
ACCESS_BACKGROUND_LOCATION    - Background location (Android 10+)

# Camera & Media
CAMERA                        - Use camera
RECORD_AUDIO                  - Record audio
READ_MEDIA_IMAGES             - Read images (Android 13+)
READ_MEDIA_VIDEO              - Read videos (Android 13+)
READ_MEDIA_AUDIO              - Read audio (Android 13+)

# Sensors
VIBRATE                       - Vibrate device
BODY_SENSORS                  - Access body sensors

# Bluetooth
BLUETOOTH                     - Use Bluetooth
BLUETOOTH_ADMIN               - Discover and pair devices
BLUETOOTH_CONNECT             - Connect to paired devices (Android 12+)
BLUETOOTH_SCAN                - Scan for devices (Android 12+)

# Phone
READ_PHONE_STATE              - Read phone state
CALL_PHONE                    - Make phone calls

# Contacts
READ_CONTACTS                 - Read contacts
WRITE_CONTACTS                - Modify contacts

# Calendar
READ_CALENDAR                 - Read calendar
WRITE_CALENDAR                - Modify calendar

# System
WAKE_LOCK                     - Prevent screen from dimming
RECEIVE_BOOT_COMPLETED        - Start on boot
FOREGROUND_SERVICE            - Run foreground services (Android 9+)

Usage:
    androidpermissions(["INTERNET", "CAMERA", "ACCESS_FINE_LOCATION"])
"""

# ===========================================================================
# PROGUARD RULES TEMPLATES
# ===========================================================================

PROGUARD_TEMPLATES = """
Common ProGuard Rules:

# Keep app classes
androidproguardrules([
    "-keep class com.myapp.** { *; }"
])

# Keep native methods
androidproguardrules([
    "-keepclasseswithmembernames class * {",
    "    native <methods>;",
    "}"
])

# Keep annotations
androidproguardrules([
    "-keepattributes *Annotation*"
])

# Suppress warnings
androidproguardrules([
    "-dontwarn org.lwjgl.**",
    "-dontwarn javax.annotation.**"
])

# Keep serializable classes
androidproguardrules([
    "-keepclassmembers class * implements java.io.Serializable {",
    "    static final long serialVersionUID;",
    "    private static final java.io.ObjectStreamField[] serialPersistentFields;",
    "    !static !transient <fields>;",
    "    private void writeObject(java.io.ObjectOutputStream);",
    "    private void readObject(java.io.ObjectInputStream);",
    "    java.lang.Object writeReplace();",
    "    java.lang.Object readResolve();",
    "}"
])
"""