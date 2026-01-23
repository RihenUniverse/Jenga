#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Core Module
Main import for .nken configuration files
"""

# Import all API functions to make them available in .nken files
from core.api import *

__all__ = [
    # Context managers
    'workspace', 'project', 'toolchain', 'filter', 'test',
    
    # Workspace configuration
    'configurations', 'platforms', 'startproject', 'location',
    
    # Project kinds
    'consoleapp', 'windowedapp', 'staticlib', 'sharedlib', 'testsuite',
    
    # Language settings
    'language', 'cppdialect', 'cdialect',
    
    # Files
    'files', 'excludefiles', 'excludemainfiles',
    
    # Precompiled Headers
    'pchheader', 'pchsource',
    
    # Directories
    'includedirs', 'libdirs', 'objdir', 'targetdir', 'targetname',
    
    # Linking
    'links', 'dependson',
    
    # Dependencies and Resources
    'dependfiles', 'embedresources',
    
    # Compiler settings
    'defines', 'optimize', 'symbols', 'warnings',
    
    # Build hooks
    'prebuild', 'postbuild', 'prelink', 'postlink',
    
    # Toolchain selection
    'usetoolchain',
    
    # Android settings
    'androidsdkpath', 'androidndkpath', 'javajdkpath',
    'androidapplicationid', 'androidversioncode', 'androidversionname',
    'androidminsdk', 'androidtargetsdk',
    'androidsign', 'androidkeystore', 'androidkeystorepass', 'androidkeyalias',
    
    # Test settings
    'testoptions', 'testfiles', 'testmainfile', 'testmaintemplate',
    
    # Other
    'systemversion',
    
    # Toolchain settings
    'cppcompiler', 'ccompiler', 'toolchaindir',
]
