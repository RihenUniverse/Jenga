#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga – Système de build cross‑plateforme pour projets C/C++ et autres.
Package principal exposant l'API publique, les commandes et les utilitaires.
"""

import sys
import types

__version__ = "2.0.0"
__author__ = "Jenga Team"
__license__ = "Proprietary"

# Exposer l'API publique directement depuis le package racine
from .Core.Api import (
    # Enums
    ProjectKind, Language, Optimization, WarningLevel,
    TargetOS, TargetArch, TargetEnv, CompilerFamily,
    # Context managers
    workspace, project, toolchain, filter, unitest, test, include, batchinclude, addtools,
    # User functions (lowercase DSL)
    configurations, platforms, targetoses, targetarchs, targetos, targetarch, platform, architecture, startproject,
    consoleapp, windowedapp, staticlib, sharedlib, testsuite, kind,
    language, cppdialect, cdialect,
    location, files, excludefiles, removefiles, excludemainfiles, removemainfiles,
    includedirs, libdirs, objdir, targetdir, targetname,
    links, dependson, dependfiles, embedresources,
    defines, optimize, symbols, warnings,
    pchheader, pchsource,
    prebuild, postbuild, prelink, postlink,
    usetoolchain,
    androidsdkpath, androidndkpath, javajdkpath,
    androidapplicationid, androidversioncode, androidversionname,
    androidminsdk, androidtargetsdk, androidcompilesdk,
    androidabis, androidproguard, androidproguardrules,
    androidassets, androidpermissions, androidnativeactivity,
    ndkversion, androidsign, androidkeystore, androidkeystorepass, androidkeyalias,
    iosbundleid, iosversion, iosminsdk,
    iossigningidentity, iosentitlements, iosappicon, iosbuildnumber,
    testoptions, testfiles, testmainfile, testmaintemplate,
    settarget, sysroot, targettriple, ccompiler, cppcompiler,
    linker, archiver, addcflag, addcxxflag, addldflag,
    cflags, cxxflags, ldflags, asmflags, arflags,
    framework, frameworkpath, librarypath, library, rpath,
    sanitize, nostdlib, nostdinc, pic, pie,
    buildoption, buildoptions,
    useproject, getprojectproperties,
    includefromdirectory, listincludes, getincludeinfo, validateincludes,
    lip, vip, getincludedprojects, generatedependencyreport, listallprojects,
    getcurrentworkspace, resetstate,
    # Tools
    addtools, usetool, listtools, gettoolinfo, validatetools,
    CreateAndroidNdkTool, CreateEmscriptenTool, CreateCustomGccTool,
    inittools,
)

# Exposer les sous-packages en tant que modules
from . import Commands
from . import Core
from . import Unitest
from . import Utils
from .GlobalToolchains import *

__all__ = [
    # Version
    '__version__',
    # API (tous les symboles publics de Api.py)
    'ProjectKind', 'Language', 'Optimization', 'WarningLevel',
    'TargetOS', 'TargetArch', 'TargetEnv', 'CompilerFamily',
    'workspace', 'project', 'toolchain', 'filter', 'unitest', 'test',
    'include', 'batchinclude', 'addtools',
    'configurations', 'platforms', 'targetoses', 'targetarchs', 'targetos', 'targetarch', 'platform', 'architecture', 'startproject',
    'consoleapp', 'windowedapp', 'staticlib', 'sharedlib', 'testsuite', 'kind',
    'language', 'cppdialect', 'cdialect',
    'location', 'files', 'excludefiles', 'removefiles', 'excludemainfiles', 'removemainfiles',
    'includedirs', 'libdirs', 'objdir', 'targetdir', 'targetname',
    'links', 'dependson', 'dependfiles', 'embedresources',
    'defines', 'optimize', 'symbols', 'warnings',
    'pchheader', 'pchsource',
    'prebuild', 'postbuild', 'prelink', 'postlink',
    'usetoolchain',
    'androidsdkpath', 'androidndkpath', 'javajdkpath',
    'androidapplicationid', 'androidversioncode', 'androidversionname',
    'androidminsdk', 'androidtargetsdk', 'androidcompilesdk',
    'androidabis', 'androidproguard', 'androidproguardrules',
    'androidassets', 'androidpermissions', 'androidnativeactivity',
    'ndkversion', 'androidsign', 'androidkeystore', 'androidkeystorepass', 'androidkeyalias',
    'iosbundleid', 'iosversion', 'iosminsdk',
    'iossigningidentity', 'iosentitlements', 'iosappicon', 'iosbuildnumber',
    'testoptions', 'testfiles', 'testmainfile', 'testmaintemplate',
    'settarget', 'sysroot', 'targettriple', 'ccompiler', 'cppcompiler',
    'linker', 'archiver', 'addcflag', 'addcxxflag', 'addldflag',
    'cflags', 'cxxflags', 'ldflags', 'asmflags', 'arflags',
    'framework', 'frameworkpath', 'librarypath', 'library', 'rpath',
    'sanitize', 'nostdlib', 'nostdinc', 'pic', 'pie',
    'buildoption', 'buildoptions',
    'useproject', 'getprojectproperties',
    'includefromdirectory', 'listincludes', 'getincludeinfo', 'validateincludes',
    'lip', 'vip', 'getincludedprojects', 'generatedependencyreport', 'listallprojects',
    'getcurrentworkspace', 'resetstate',
    'addtools', 'usetool', 'listtools', 'gettoolinfo', 'validatetools',
    'CreateAndroidNdkTool', 'CreateEmscriptenTool', 'CreateCustomGccTool',
    'inittools',
    # Sous-packages
    'Commands', 'Core', 'Unitest', 'Utils',
    # Toolchain
    'ToolchainAndroidNDK', 'ToolchainClangCl', 'ToolchainClangCrossLinux', 'ToolchainClangMinGW',
    'ToolchainEmscripten', 'ToolchainHostClang', 'ToolchainMinGW', 'ToolchainZigLinuxX64',
]

# Initialisation du système de tools au chargement du package
inittools()

# Backward compatibility:
# Some previously generated entry points import `Jenga.Jenga:main`.
# Provide a lightweight module alias without importing `Jenga.jenga` eagerly.
_legacy_module_name = __name__ + ".Jenga"
if _legacy_module_name not in sys.modules:
    _legacy_module = types.ModuleType(_legacy_module_name)

    def _legacy_main(*args, **kwargs):
        from .jenga import main as _main
        return _main(*args, **kwargs)

    _legacy_module.main = _legacy_main
    sys.modules[_legacy_module_name] = _legacy_module
