#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Create Command
Crée des workspaces, projets et fichiers avec structure professionnelle.
"""

import os
import sys
import re
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Set
import argparse

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

COMPANY_NAME = "Rihen"
COPYRIGHT_YEAR = "2024-2026"
VERSION = "1.0.2"
LICENSE_TYPE = "Proprietary License - Free to use and modify"

# Templates for file headers and footers
HEADER_TEMPLATE = {
    'py': """{shebang}
""",
    'txt': """{shebang}
""",
    'jenga': """{shebang}
""",
    'cpp': "",
    'h': "",
    'hpp': "",
    'c': "",
    'm': "",
    'mm': "",
    'inl': "",
    'md': "",
    'cmake': "",
    'xml': "",
    'json': "",
}

FOOTER_TEMPLATE = {
    'py': """\n# END OF FILE: {filename}\n""",
    'txt': """\n# END OF FILE: {filename}\n""",
    'jenga': """\n# END OF FILE: {filename}\n""",
    'cpp': """\n// END OF FILE: {filename}\n""",
    'h': """\n// END OF FILE: {filename}\n""",
    'hpp': """\n// END OF FILE: {filename}\n""",
    'c': """\n// END OF FILE: {filename}\n""",
    'm': """\n// END OF FILE: {filename}\n""",
    'mm': """\n// END OF FILE: {filename}\n""",
    'inl': """\n// END OF FILE: {filename}\n""",
    'md': """\n<!-- END OF FILE: {filename} -->\n""",
    'cmake': """\n# END OF FILE: {filename}\n""",
    'xml': """\n<!-- END OF FILE: {filename} -->\n""",
    'json': """\n/* END OF FILE: {filename} */\n""",
}

COMMENT_STYLES = {
    'cpp': ('//', '//'),
    'h': ('//', '//'),
    'hpp': ('//', '//'),
    'cpp_header': ('//', '//'),
    'c': ('//', '//'),
    'm': ('//', '//'),
    'mm': ('//', '//'),
    'inl': ('//', '//'),
    'py': ('#', '#'),
    'jenga': ('#', '#'),
    'txt': ('#', '#'),
    'md': ('<!--', '-->'),
    'cmake': ('#', '#'),
    'xml': ('<!--', '-->'),
    'json': ('/*', '*/'),
}

# Project types supported by Jenga API
PROJECT_TYPES = {
    'consoleapp': {
        'name': 'Console Application',
        'api_function': 'consoleapp()',
        'kind': 'CONSOLE_APP',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': True,
        'is_executable': True,
        'use_pch': False,
    },
    'windowedapp': {
        'name': 'Windowed Application',
        'api_function': 'windowedapp()',
        'kind': 'WINDOWED_APP',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': True,
        'is_executable': True,
        'use_pch': False,
    },
    'staticlib': {
        'name': 'Static Library',
        'api_function': 'staticlib()',
        'kind': 'STATIC_LIB',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': False,
        'is_executable': False,
        'use_pch': True,
    },
    'sharedlib': {
        'name': 'Shared Library',
        'api_function': 'sharedlib()',
        'kind': 'SHARED_LIB',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': False,
        'is_executable': False,
        'use_pch': True,
    },
    'androidapp': {
        'name': 'Android Application',
        'api_function': 'windowedapp()',
        'kind': 'WINDOWED_APP',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': True,
        'is_executable': True,
        'platforms': ['Android'],
        'use_pch': False,
    },
    'iosapp': {
        'name': 'iOS Application',
        'api_function': 'windowedapp()',
        'kind': 'WINDOWED_APP',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': True,
        'is_executable': True,
        'platforms': ['iOS'],
        'use_pch': False,
    },
    'capp': {
        'name': 'C Application',
        'api_function': 'consoleapp()',
        'kind': 'CONSOLE_APP',
        'default_language': 'C',
        'default_std': 'C11',
        'create_main': True,
        'is_executable': True,
        'use_pch': False,
    },
    'clib': {
        'name': 'C Library',
        'api_function': 'staticlib()',
        'kind': 'STATIC_LIB',
        'default_language': 'C',
        'default_std': 'C11',
        'create_main': False,
        'is_executable': False,
        'use_pch': True,
    },
}

# Programming languages
LANGUAGES = {
    'C': {
        'name': 'C',
        'standards': ['C89', 'C90', 'C99', 'C11', 'C17', 'C23'],
        'default_std': 'C11',
        'extensions': ['.c', '.h'],
    },
    'C++': {
        'name': 'C++',
        'standards': ['C++98', 'C++03', 'C++11', 'C++14', 'C++17', 'C++20', 'C++23', 'C++26'],
        'default_std': 'C++17',
        'extensions': ['.cpp', '.cxx', '.cc', '.hpp', '.hxx', '.hh', '.h'],
    },
    'Objective-C': {
        'name': 'Objective-C',
        'standards': ['Objective-C'],
        'default_std': 'Objective-C',
        'extensions': ['.m', '.h'],
    },
    'Objective-C++': {
        'name': 'Objective-C++',
        'standards': ['Objective-C++'],
        'default_std': 'Objective-C++',
        'extensions': ['.mm', '.h'],
    },
}

# Platforms and architectures
PLATFORMS = ["Windows", "Linux", "MacOS", "Android", "iOS", "Emscripten"]
ARCHITECTURES = ["x86", "x64", "ARM", "ARM64", "WASM"]

# Build configurations
CONFIGURATIONS = ["Debug", "Release", "Dist", "Profile", "Coverage"]

# Compilers and toolchains
COMPILERS = {
    'clang++': {
        'name': 'Clang/LLVM',
        'cc': 'clang',
        'cxx': 'clang++',
        'linker': 'clang++',
        'archiver': 'ar',
        'flags': {
            'common': ['-Wall', '-Wextra', '-Wpedantic'],
            'debug': ['-g', '-O0', '-DDEBUG', '-D_DEBUG'],
            'release': ['-O3', '-DNDEBUG', '-DRELEASE'],
            'debug_gdb': ['-ggdb', '-g3', '-O0', '-DDEBUG', '-D_DEBUG'],
            'debug_extra': ['-g', '-O0', '-DDEBUG', '-D_DEBUG', '-fsanitize=address', '-fno-omit-frame-pointer'],
        }
    },
    'g++': {
        'name': 'GNU GCC',
        'cc': 'gcc',
        'cxx': 'g++',
        'linker': 'g++',
        'archiver': 'ar',
        'flags': {
            'common': ['-Wall', '-Wextra'],
            'debug': ['-g', '-O0', '-DDEBUG', '-D_DEBUG'],
            'release': ['-O3', '-DNDEBUG', '-DRELEASE'],
            'debug_gdb': ['-ggdb', '-g3', '-O0', '-DDEBUG', '-D_DEBUG'],
            'debug_extra': ['-g', '-O0', '-DDEBUG', '-D_DEBUG', '-fsanitize=address', '-fno-omit-frame-pointer'],
        }
    },
    'msvc': {
        'name': 'Microsoft Visual C++',
        'cc': 'cl',
        'cxx': 'cl',
        'linker': 'link',
        'archiver': 'lib',
        'flags': {
            'common': ['/W4', '/EHsc'],
            'debug': ['/Zi', '/Od', '/MDd', '/DDEBUG', '/D_DEBUG'],
            'release': ['/O2', '/MD', '/DNDEBUG', '/DRELEASE'],
            'debug_gdb': ['/Zi', '/Od', '/MDd', '/DDEBUG', '/D_DEBUG'],
            'debug_extra': ['/Zi', '/Od', '/MDd', '/DDEBUG', '/D_DEBUG', '/fsanitize=address'],
        }
    },
}

# Default namespaces based on project type
DEFAULT_NAMESPACES = {
    'game': ['game', 'core', 'utils', 'graphics', 'audio', 'physics'],
    'engine': ['engine', 'core', 'render', 'math', 'input', 'platform'],
    'library': ['lib', 'core', 'utils', 'api', 'internal'],
    'app': ['app', 'core', 'ui', 'services', 'models'],
    'tool': ['tool', 'core', 'cli', 'utils', 'io'],
}

# Platform-specific configurations
PLATFORM_CONFIGS = {
    'Windows': {
        'defines': ['_WIN32', '_WINDOWS', 'WIN32_LEAN_AND_MEAN'],
        'links': ['kernel32', 'user32', 'gdi32', 'winspool', 'shell32', 'ole32', 'oleaut32', 'uuid', 'comdlg32', 'advapi32'],
        'frameworks': [],
    },
    'Linux': {
        'defines': ['_LINUX', '__linux__', '_POSIX_C_SOURCE=200809L'],
        'links': ['pthread', 'dl', 'm', 'rt'],
        'frameworks': [],
    },
    'MacOS': {
        'defines': ['_MACOS', '__APPLE__', '_DARWIN_C_SOURCE'],
        'links': [],
        'frameworks': ['Cocoa', 'Foundation', 'CoreFoundation', 'CoreGraphics', 'CoreServices', 'Security', 'SystemConfiguration'],
    },
    'Android': {
        'defines': ['_ANDROID', '__ANDROID__', 'ANDROID'],
        'links': ['log', 'android', 'EGL', 'GLESv3', 'GLESv2', 'OpenSLES'],
        'frameworks': [],
    },
    'iOS': {
        'defines': ['_IOS', '__IOS__', 'IOS'],
        'links': [],
        'frameworks': ['UIKit', 'Foundation', 'CoreGraphics', 'QuartzCore', 'CoreFoundation', 'Security', 'SystemConfiguration'],
    },
    'Emscripten': {
        'defines': ['_EMSCRIPTEN', '__EMSCRIPTEN__'],
        'links': ['GL', 'SDL2'],
        'frameworks': [],
    },
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_file_header(filename: str, description: str, file_type: str = None, include_shebang: bool = False) -> str:
    """Generate a file header with copyright and metadata."""
    if file_type is None:
        file_type = Path(filename).suffix.lstrip('.')
        if not file_type:
            file_type = 'txt'
    
    comment_style = COMMENT_STYLES.get(file_type, ('//', '//'))
    comment_start, comment_end = comment_style
    
    # Shebang for executable Python files
    shebang = ''
    if include_shebang and file_type in ['py', 'jenga']:
        shebang = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\n'
    
    # Determine content based on file type
    if file_type in ['cpp', 'h', 'hpp', 'c', 'm', 'mm', 'inl']:
        content = f'''{comment_start}
{comment_start} {filename}
{comment_start} {description}
{comment_start} {'=' * 60}
{comment_start} Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{comment_start} {LICENSE_TYPE}
{comment_start}
{comment_start} Generated by Jenga Build System v{VERSION}
{comment_start} Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{comment_start}
'''
    elif file_type in ['py', 'jenga', 'txt', 'cmake']:
        content = f'''{shebang}{comment_start}
{comment_start} {filename}
{comment_start} {description}
{comment_start} {'=' * 60}
{comment_start} Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{comment_start} {LICENSE_TYPE}
{comment_start}
{comment_start} Generated by Jenga Build System v{VERSION}
{comment_start} Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{comment_start}
'''
    elif file_type == 'md':
        content = f'''<!--
{filename}
{description}
{'=' * 60}
Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{LICENSE_TYPE}

Generated by Jenga Build System v{VERSION}
Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-->

'''
    elif file_type == 'xml':
        content = f'''<!--
{filename}
{description}
{'=' * 60}
Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{LICENSE_TYPE}

Generated by Jenga Build System v{VERSION}
Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-->

'''
    elif file_type == 'json':
        content = f'''/*
{filename}
{description}
{'=' * 60}
Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{LICENSE_TYPE}

Generated by Jenga Build System v{VERSION}
Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
*/

'''
    else:
        content = f'''{comment_start}
{comment_start} {filename}
{comment_start} {description}
{comment_start} {'=' * 60}
{comment_start} Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{comment_start} {LICENSE_TYPE}
{comment_start}
{comment_start} Generated by Jenga Build System v{VERSION}
{comment_start} Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{comment_start}
'''
    
    return content


def get_file_footer(filename: str, file_type: str = None) -> str:
    """Generate a file footer."""
    if file_type is None:
        file_type = Path(filename).suffix.lstrip('.')
        if not file_type:
            file_type = 'txt'
    
    footer_template = FOOTER_TEMPLATE.get(file_type, '\n# END OF FILE: {filename}\n')
    return footer_template.format(filename=filename)


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask a yes/no question with default value."""
    default_str = 'Y/n' if default else 'y/N'
    response = input(f"{question} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    return response in ['y', 'yes', 'oui', 'o']


def ask_choice(question: str, choices: List[str], default: int = 0) -> str:
    """Ask user to choose from a list."""
    print(f"\n{question}:")
    for i, choice in enumerate(choices):
        print(f"  {i+1}. {choice}")
    
    while True:
        try:
            response = input(f"Choice [1-{len(choices)}] (default {default+1}): ").strip()
            if not response:
                return choices[default]
            
            idx = int(response) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
            else:
                print(f"Please enter a number between 1 and {len(choices)}")
        except ValueError:
            print("Please enter a valid number")


def ask_multi_choice(question: str, choices: List[str], defaults: List[str] = None) -> List[str]:
    """Ask user to select multiple choices."""
    print(f"\n{question}:")
    for i, choice in enumerate(choices):
        default_mark = "✓" if defaults and choice in defaults else " "
        print(f"  [{default_mark}] {i+1}. {choice}")
    
    print("\nEnter numbers separated by commas (e.g., '1,3,5') or 'all' for all")
    
    while True:
        response = input("Selection: ").strip().lower()
        
        if not response and defaults:
            return defaults
        
        if response == 'all':
            return choices
        
        try:
            indices = [int(idx.strip()) - 1 for idx in response.split(',')]
            selected = [choices[i] for i in indices if 0 <= i < len(choices)]
            
            if selected:
                return selected
            else:
                print("Please enter valid numbers")
        except ValueError:
            print("Please enter numbers separated by commas")


def ask_string(question: str, default: str = "", required: bool = True) -> str:
    """Ask user for string input."""
    while True:
        if default:
            response = input(f"{question} [{default}]: ").strip()
        else:
            response = input(f"{question}: ").strip()
        
        if not response and default:
            return default
        
        if not response and required:
            print("This field is required")
        else:
            return response


def ask_namespace(project_name: str) -> Tuple[str, List[str]]:
    """Ask for namespace configuration."""
    print("\n📦 Namespace Configuration:")
    
    # Ask if use namespace
    use_namespace = ask_yes_no("Use C++ namespace?", default=True)
    if not use_namespace:
        return "", []
    
    # Main namespace
    default_ns = project_name.lower().replace('-', '_').replace(' ', '_')
    main_ns = ask_string(f"Main namespace", default=default_ns, required=False)
    if not main_ns:
        main_ns = default_ns
    
    # Sub-namespaces
    print("\nDo you want to add sub-namespaces? (e.g., core, utils, graphics)")
    sub_namespaces = []
    if ask_yes_no("Add sub-namespaces?", default=False):
        while True:
            sub_ns = input("Enter sub-namespace (empty to finish): ").strip()
            if not sub_ns:
                break
            sub_namespaces.append(sub_ns)
    
    return main_ns, sub_namespaces


def ask_compiler_configuration() -> str:
    """Ask user for compiler configuration."""
    print("\n🔧 Compiler Configuration:")
    print("Select default compiler for the workspace:")
    
    compiler_keys = list(COMPILERS.keys())
    compiler_names = [COMPILERS[c]['name'] for c in compiler_keys]
    
    selected = ask_choice("Compiler", compiler_names, default=0)
    
    # Find key by name
    for key, info in COMPILERS.items():
        if info['name'] == selected:
            return key
    
    return 'clang++'  # Default


def ask_debug_level() -> List[str]:
    """Ask for debug configuration level."""
    print("\n🐛 Debug Configuration:")
    print("Select debug levels to enable:")
    
    debug_levels = [
        ("Basic", ["-g"], "Basic debug symbols"),
        ("GDB", ["-ggdb", "-g3"], "Enhanced debug symbols for GDB"),
        ("Extra", ["-fsanitize=address", "-fno-omit-frame-pointer"], "Address sanitizer and frame pointers"),
    ]
    
    choices = [f"{name}: {desc}" for name, _, desc in debug_levels]
    selected = ask_multi_choice("Debug levels", choices, defaults=[choices[0]])
    
    # Extract flags
    flags = []
    for choice in selected:
        for name, flag_list, desc in debug_levels:
            if choice.startswith(name):
                flags.extend(flag_list)
    
    return list(set(flags))  # Remove duplicates


def create_directory_structure(base_path: Path, structure: Dict[str, List[str]]) -> None:
    """Create directory structure."""
    for dir_path, subdirs in structure.items():
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  📁 Created: {dir_path}/")
        
        for subdir in subdirs:
            subdir_path = full_path / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"  📁 Created: {dir_path}/{subdir}/")


def format_indent(text: str, indent_level: int = 1, indent_size: int = 4) -> str:
    """Format text with proper indentation."""
    indent = ' ' * (indent_level * indent_size)
    lines = text.split('\n')
    indented_lines = []
    
    for line in lines:
        if line.strip():
            indented_lines.append(indent + line)
        else:
            indented_lines.append('')
    
    return '\n'.join(indented_lines)


# ============================================================================
# WORKSPACE CREATION
# ============================================================================

def create_workspace_interactive() -> int:
    """Interactive workspace creation with all options."""
    print("\n" + "="*60)
    print("🏗️  JENGA WORKSPACE CREATION WIZARD")
    print("="*60)
    
    # Workspace name
    workspace_name = ask_string("📝 Workspace name", required=True)
    
    # Location
    location = ask_string("📁 Location", default=".")
    workspace_dir = Path(location) / workspace_name
    
    if workspace_dir.exists():
        print(f"❌ Error: Directory '{workspace_dir}' already exists")
        return 1
    
    # Ask if create main project
    print("\n📦 Main Project Configuration:")
    create_main_project = ask_yes_no("Create main project with same name?", default=True)
    
    main_project_type = "consoleapp"
    main_project_namespace = workspace_name.lower()
    sub_namespaces = []
    project_name = workspace_name
    project_location = "."
    
    if create_main_project:
        # Project location
        print(f"\n📂 Project Location Configuration:")
        print(f"By default, project will be created in: {workspace_name}/")
        if ask_yes_no("Create project in subdirectory?", default=False):
            project_location = ask_string("Project subdirectory", default=project_name)
        
        # Project type
        print("\n🎯 Select main project type:")
        project_type_keys = list(PROJECT_TYPES.keys())
        project_type_names = [PROJECT_TYPES[pt]['name'] for pt in project_type_keys]
        main_project_type = ask_choice("Project type", project_type_names, default=0)
        
        # Map back to key
        for key, info in PROJECT_TYPES.items():
            if info['name'] == main_project_type:
                main_project_type = key
                break
        
        # Language configuration
        print("\n🔤 Language Configuration:")
        language_keys = list(LANGUAGES.keys())
        language_names = [LANGUAGES[lang]['name'] for lang in language_keys]
        language = ask_choice("Programming language", language_names, default=1)  # Default C++
        
        # Map back to key
        for key, info in LANGUAGES.items():
            if info['name'] == language:
                language = key
                break
        
        # Standard
        standards = LANGUAGES[language]['standards']
        default_std = LANGUAGES[language]['default_std']
        default_idx = standards.index(default_std) if default_std in standards else 0
        standard = ask_choice(f"{language} standard", standards, default=default_idx)
        
        # Namespace configuration (only for C++ and Objective-C++)
        if language in ["C++", "Objective-C++"]:
            main_project_namespace, sub_namespaces = ask_namespace(project_name)
        else:
            main_project_namespace = ""
            sub_namespaces = []
    else:
        language = "C++"
        standard = "C++17"
    
    # Platforms
    print("\n🌍 Target Platforms:")
    default_platforms = ["Windows", "Linux", "MacOS"]
    platforms = ask_multi_choice(
        "Select target platforms",
        PLATFORMS,
        defaults=default_platforms
    )
    
    # Architectures
    print("\n⚙️  Target Architectures:")
    architectures = ask_multi_choice(
        "Select target architectures",
        ARCHITECTURES,
        defaults=["x64"]
    )
    
    # Configurations
    print("\n⚡ Build Configurations:")
    configurations = ask_multi_choice(
        "Select build configurations",
        CONFIGURATIONS,
        defaults=["Debug", "Release"]
    )
    
    # Debug level if Debug is selected
    debug_flags = []
    if "Debug" in configurations:
        debug_flags = ask_debug_level()
    
    # Toolchain configuration
    compiler_choice = ask_compiler_configuration()
    
    # Summary
    print("\n" + "="*60)
    print("📋 CREATION SUMMARY")
    print("="*60)
    print(f"Workspace:      {workspace_name}")
    print(f"Location:       {workspace_dir}")
    print(f"Main Project:   {'Yes' if create_main_project else 'No'}")
    
    if create_main_project:
        print(f"Project Name:   {project_name}")
        print(f"Project Type:   {PROJECT_TYPES[main_project_type]['name']}")
        print(f"Project Loc:    {project_location}/")
        print(f"Language:       {language} ({standard})")
        if main_project_namespace:
            print(f"Namespace:      {main_project_namespace}")
            if sub_namespaces:
                print(f"Sub-namespaces: {', '.join(sub_namespaces)}")
    
    print(f"Platforms:      {', '.join(platforms)}")
    print(f"Architectures:  {', '.join(architectures)}")
    print(f"Configurations: {', '.join(configurations)}")
    print(f"Compiler:       {COMPILERS[compiler_choice]['name']}")
    if debug_flags:
        print(f"Debug Flags:    {' '.join(debug_flags)}")
    print("="*60)
    
    # Confirm
    if not ask_yes_no("\nCreate workspace with these settings?", default=True):
        print("❌ Creation cancelled")
        return 0
    
    # Create workspace
    return create_workspace(
        workspace_name=workspace_name,
        location=location,
        create_main_project=create_main_project,
        main_project_type=main_project_type,
        main_project_namespace=main_project_namespace,
        sub_namespaces=sub_namespaces,
        project_name=project_name,
        project_location=project_location,
        language=language,
        standard=standard,
        platforms=platforms,
        architectures=architectures,
        configurations=configurations,
        compiler_choice=compiler_choice,
        debug_flags=debug_flags
    )


def create_workspace(
    workspace_name: str,
    location: str = ".",
    create_main_project: bool = True,
    main_project_type: str = "consoleapp",
    main_project_namespace: str = "",
    sub_namespaces: List[str] = None,
    project_name: str = None,
    project_location: str = ".",
    language: str = "C++",
    standard: str = "C++17",
    platforms: List[str] = None,
    architectures: List[str] = None,
    configurations: List[str] = None,
    compiler_choice: str = "clang++",
    debug_flags: List[str] = None
) -> int:
    """Create a new workspace with complete structure."""
    
    workspace_dir = Path(location) / workspace_name
    
    if workspace_dir.exists():
        print(f"❌ Error: Directory '{workspace_dir}' already exists")
        return 1
    
    print(f"\n📁 Creating workspace '{workspace_name}'...")
    
    # Default values
    if sub_namespaces is None:
        sub_namespaces = []
    if project_name is None:
        project_name = workspace_name
    if platforms is None:
        platforms = ["Windows", "Linux", "MacOS"]
    if architectures is None:
        architectures = ["x64"]
    if configurations is None:
        configurations = ["Debug", "Release"]
    if debug_flags is None:
        debug_flags = []
    
    compiler_info = COMPILERS[compiler_choice]
    
    # Create directory structure
    workspace_dir.mkdir(parents=True)
    
    # Main directories with subdirectories for assets
    create_directory_structure(workspace_dir, {
        "assets": ["resources", "images/textures", "images/hdri", "models", "audio", "fonts", "shaders"],
        "docs": ["api", "architecture", "tutorials"],
        "externals": [],
        "config": [],
        ".github/workflows": [],
    })
    
    # Create workspace .jenga file
    create_workspace_jenga_file(
        workspace_dir=workspace_dir,
        workspace_name=workspace_name,
        platforms=platforms,
        architectures=architectures,
        configurations=configurations,
        compiler_choice=compiler_choice,
        compiler_info=compiler_info,
        debug_flags=debug_flags,
        create_main_project=create_main_project,
        main_project_type=main_project_type,
        project_name=project_name,
        project_location=project_location
    )
    
    # Create main project if requested
    if create_main_project:
        # Determine project directory path
        if project_location == ".":
            project_dir = workspace_dir / project_name
        else:
            project_dir = workspace_dir / project_location / project_name
        
        project_dir.mkdir(parents=True, exist_ok=True)
        print(f"  📁 Created project directory: {project_dir.relative_to(workspace_dir)}/")
        
        # Create project structure with project-name subdirectories
        create_project_directory_structure(project_dir, project_name)
        
        # Create project files
        create_project_jenga_file(
            project_dir=project_dir,
            project_name=project_name,
            project_type=main_project_type,
            main_namespace=main_project_namespace,
            sub_namespaces=sub_namespaces,
            language=language,
            standard=standard,
            platforms=platforms,
            configurations=configurations,
            compiler_choice=compiler_choice,
            compiler_info=compiler_info,
            debug_flags=debug_flags,
            workspace_dir=workspace_dir
        )
        
        # Create source files
        create_project_source_files(
            project_dir=project_dir,
            project_name=project_name,
            project_type=main_project_type,
            language=language,
            main_namespace=main_project_namespace,
            sub_namespaces=sub_namespaces,
            standard=standard
        )
    
    # Create additional files
    create_workspace_additional_files(workspace_dir, workspace_name)
    
    # Print summary
    print_workspace_creation_summary(
        workspace_dir=workspace_dir,
        workspace_name=workspace_name,
        create_main_project=create_main_project,
        project_name=project_name if create_main_project else None,
        main_project_type=main_project_type if create_main_project else None,
        project_location=project_location if create_main_project else None,
        compiler_info=compiler_info
    )
    
    return 0


def create_project_directory_structure(project_dir: Path, project_name: str) -> None:
    """Create standard project directory structure with project-name subdirectories."""
    create_directory_structure(project_dir, {
        "include": [project_name],
        "src": [project_name],
        "pch": [],
        "tests": [],
        "resources": [],
        "docs": [],
    })


def create_workspace_jenga_file(
    workspace_dir: Path,
    workspace_name: str,
    platforms: List[str],
    architectures: List[str],
    configurations: List[str],
    compiler_choice: str,
    compiler_info: Dict[str, Any],
    debug_flags: List[str],
    create_main_project: bool = False,
    main_project_type: str = None,
    project_name: str = None,
    project_location: str = None
) -> None:
    """Create workspace .jenga file."""
    
    content = get_file_header(
        filename=f"{workspace_name}.jenga",
        description=f"{workspace_name} Workspace Configuration",
        file_type="jenga",
        include_shebang=True
    )
    
    content += '''from Jenga.core.api import *

'''
    
    content += f'''with workspace("{workspace_name}"):
    # Build configurations
    configurations({configurations})
    
    # Target platforms
    platforms({platforms})
    '''
    
    # Add startup project if it's an executable
    if create_main_project and main_project_type and PROJECT_TYPES[main_project_type]['is_executable']:
        content += f'''
    # Startup project
    startproject("{project_name}")'''
    
    content += '''
    
    # Default toolchain
    with toolchain("default", "''' + compiler_choice + '''"):'''
    
    # Add compiler paths
    if compiler_info['cxx']:
        content += f'''
        cppcompiler("{compiler_info['cxx']}")'''
    if compiler_info['cc']:
        content += f'''
        ccompiler("{compiler_info['cc']}")'''
    if compiler_info['linker']:
        content += f'''
        linker("{compiler_info['linker']}")'''
    if compiler_info['archiver']:
        content += f'''
        archiver("{compiler_info['archiver']}")'''
    
    # Add common flags
    if compiler_info['flags']['common']:
        content += f'''
        
        # Common flags
        cflags({compiler_info['flags']['common']})
        cxxflags({compiler_info['flags']['common']})'''
    
    # Add platform-specific configurations
    content += '''
        
        # Platform-specific configurations'''
    
    for platform in platforms:
        if platform in PLATFORM_CONFIGS:
            config = PLATFORM_CONFIGS[platform]
            content += f'''
        with filter("system:{platform}"):
            # {platform}-specific settings
            defines({config['defines']})'''
            
            if config['links']:
                content += f'''
            links({config['links']})'''
            
            if platform in ["MacOS", "iOS"] and config['frameworks']:
                for framework in config['frameworks']:
                    content += f'''
            framework("{framework}")'''
    
    # Add build configuration-specific flags
    content += '''
    
    # Build configuration-specific flags'''
    
    for config in configurations:
        config_lower = config.lower()
        if config_lower in compiler_info['flags']:
            content += f'''
        with filter("configurations:{config}"):
            cflags({compiler_info['flags'][config_lower]})
            cxxflags({compiler_info['flags'][config_lower]})'''
        elif config == "Debug" and debug_flags:
            # Use custom debug flags
            debug_all_flags = compiler_info['flags']['debug'] + debug_flags
            content += f'''
        with filter("configurations:Debug"):
            cflags({debug_all_flags})
            cxxflags({debug_all_flags})'''
    
    # Include main project if created
    if create_main_project and project_name:
        if project_location != ".":
            content += f'''
    
    # Main project
    addprojects("{project_location}/{project_name}/{project_name}.jenga", ["{project_name}"])'''
        else:
            content += f'''
    
    # Main project
    addprojects("{project_name}/{project_name}.jenga", ["{project_name}"])'''
    
    content += get_file_footer(f"{workspace_name}.jenga", "jenga")
    
    (workspace_dir / f"{workspace_name}.jenga").write_text(content, encoding='utf-8')
    print(f"✅ Created: {workspace_name}.jenga")


def create_workspace_additional_files(workspace_dir: Path, workspace_name: str) -> None:
    """Create additional workspace files."""
    
    # README.md
    readme_content = get_file_header(
        filename="README.md",
        description=f"{workspace_name} - Project Documentation",
        file_type="md"
    )
    
    readme_content += f'''# {workspace_name}

## Overview
This project was created with Jenga Build System v{VERSION}.

## Project Structure

```
{workspace_name}/
├── {workspace_name}.jenga          # Workspace configuration
├── assets/                         # Assets directory
│   ├── resources/                  # Game/resources files
│   ├── images/textures/            # Texture images
│   ├── images/hdri/                # HDRI environment maps
│   ├── models/                     # 3D models
│   ├── audio/                      # Audio files
│   ├── fonts/                      # Font files
│   └── shaders/                    # Shader files
├── docs/                           # Documentation
│   ├── api/                        # API documentation
│   ├── architecture/               # Architecture docs
│   └── tutorials/                  # Tutorials
├── externals/                      # External dependencies
├── config/                         # Configuration files
├── .github/workflows/              # CI/CD workflows
├── README.md                       # This file
├── .gitignore                      # Git ignore
└── LICENSE                         # License
```

## Getting Started

### Prerequisites
- Python 3.7+
- C++ compiler (GCC, Clang, or MSVC)
- Jenga Build System (`pip install jenga-build-system`)

### Build Commands
```bash
# Build all projects
jenga build

# Build specific configuration
jenga build --config Release

# Build specific project
jenga build --project {workspace_name}

# Run application
jenga run

# Run tests
jenga run --project {workspace_name}_Tests

# Clean build artifacts
jenga clean

# Generate IDE project files
jenga gen
```

## Development

### Adding New Projects
```bash
# From workspace root
jenga create project MyLibrary --type staticlib
jenga create project MyApp --type consoleapp --location apps/
```

### Adding Source Files
```bash
# From project directory
jenga create file MyClass --type class
jenga create file Constants --type enum
jenga create file Utilities --type header
```

## License
{LICENSE_TYPE}
Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}
'''
    
    readme_content += get_file_footer("README.md", "md")
    (workspace_dir / "README.md").write_text(readme_content, encoding='utf-8')
    print(f"✅ Created: README.md")
    
    # .gitignore
    gitignore_content = '''# Jenga Build System
Build/
.jenga/
bin/
obj/
out/

# IDE
.vscode/
.idea/
.vs/
*.suo
*.user
*.sdf
*.opendb

# OS
.DS_Store
Thumbs.db
*.swp
*~

# Compiled files
*.o
*.obj
*.exe
*.dll
*.so
*.dylib
*.a
*.lib
*.pdb
*.idb
*.ipdb
*.iobj

# Precompiled headers
*.pch
*.gch

# Temporary files
*.tmp
*.temp
*.cache

# Logs
*.log
*.tlog
*.lastbuildstate

# Coverage
*.gcda
*.gcno
*.gcov

# Profiling
*.profdata
*.profraw

# Asset files (uncomment if needed)
# assets/*.psd
# assets/*.blend
# assets/*.fbx
'''
    
    (workspace_dir / ".gitignore").write_text(gitignore_content, encoding='utf-8')
    print(f"✅ Created: .gitignore")
    
    # LICENSE
    license_content = f'''{COMPANY_NAME} PROPRIETARY LICENSE

Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.

IMPORTANT: READ CAREFULLY

This Proprietary License Agreement ("Agreement") is a legal agreement between you 
(either an individual or a single entity) and {COMPANY_NAME} for the software 
product and associated documentation ("Software").

BY USING THE SOFTWARE, YOU AGREE TO BE BOUND BY THE TERMS OF THIS AGREEMENT.

1. GRANT OF LICENSE
{COMPANY_NAME} grants you a non-exclusive, worldwide, royalty-free license to:
   a) Use the Software for any purpose, personal or commercial
   b) Modify the source code to create derivative works
   c) Distribute the Software or derivative works

   CONDITIONS:
   - You must include this license in all distributions
   - You must preserve all copyright notices
   - You cannot remove license headers from source files

2. RESTRICTIONS
You may not:
   a) Sell the Software as a standalone product
   b) Grant sublicenses to others
   c) Use the {COMPANY_NAME} name for endorsement without permission
   d) Remove or alter any proprietary notices

3. NO WARRANTY
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

4. LIMITATION OF LIABILITY
IN NO EVENT SHALL {COMPANY_NAME} BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
THE SOFTWARE.

5. TERMINATION
This license is effective until terminated. Your rights under this license will 
terminate automatically without notice if you fail to comply with any term(s).

For questions about this license, contact: rihen.universe@gmail.com
'''
    
    (workspace_dir / "LICENSE").write_text(license_content, encoding='utf-8')
    print(f"✅ Created: LICENSE")


def print_workspace_creation_summary(
    workspace_dir: Path,
    workspace_name: str,
    create_main_project: bool,
    project_name: str = None,
    main_project_type: str = None,
    project_location: str = None,
    compiler_info: Dict[str, Any] = None
) -> None:
    """Print workspace creation summary."""
    
    print(f"\n✅ Workspace '{workspace_name}' created successfully!")
    print(f"   Location: {workspace_dir.absolute()}")
    
    if compiler_info:
        print(f"   Compiler: {compiler_info['name']}")
    
    print(f"\n📂 Structure created:")
    print(f"   {workspace_name}/")
    print(f"   ├── {workspace_name}.jenga          # Workspace configuration")
    print(f"   ├── assets/                        # Assets directory")
    print(f"   │   ├── resources/                 # Resources")
    print(f"   │   ├── images/textures/           # Textures")
    print(f"   │   ├── images/hdri/               # HDRI maps")
    print(f"   │   ├── models/                    # 3D models")
    print(f"   │   ├── audio/                     # Audio files")
    print(f"   │   ├── fonts/                     # Fonts")
    print(f"   │   └── shaders/                   # Shaders")
    print(f"   ├── docs/                          # Documentation")
    print(f"   ├── externals/                     # External dependencies")
    print(f"   ├── config/                        # Configuration files")
    print(f"   ├── .github/workflows/             # CI/CD")
    print(f"   ├── README.md                      # Documentation")
    print(f"   ├── .gitignore                     # Git ignore")
    print(f"   └── LICENSE                        # License")
    
    if create_main_project and project_name:
        project_type_name = PROJECT_TYPES[main_project_type]['name']
        if project_location != ".":
            print(f"\n   Project '{project_name}' ({project_type_name}):")
            print(f"   ├── {project_location}/{project_name}/     # Project directory")
            print(f"   │   ├── {project_name}.jenga              # Project configuration")
            print(f"   │   ├── src/{project_name}/               # Source files")
            print(f"   │   ├── include/{project_name}/           # Public headers")
            print(f"   │   ├── pch/                             # Precompiled headers")
            print(f"   │   ├── tests/                           # Unit tests")
            print(f"   │   ├── resources/                       # Resource files")
            print(f"   │   └── docs/                            # Documentation")
        else:
            print(f"\n   Project '{project_name}' ({project_type_name}):")
            print(f"   ├── {project_name}/                      # Project directory")
            print(f"   │   ├── {project_name}.jenga            # Project configuration")
            print(f"   │   ├── src/{project_name}/             # Source files")
            print(f"   │   ├── include/{project_name}/         # Public headers")
            print(f"   │   ├── pch/                           # Precompiled headers")
            print(f"   │   ├── tests/                         # Unit tests")
            print(f"   │   ├── resources/                     # Resource files")
            print(f"   │   └── docs/                          # Documentation")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. cd {workspace_name}")
    
    if create_main_project and project_name:
        print(f"   2. jenga build                      # Build the project")
        print(f"   3. jenga run                        # Run the application")
        print(f"   4. jenga create project Library     # Add another project")
    else:
        print(f"   2. jenga create project App         # Create your first project")
        print(f"   3. jenga build                      # Build the project")
        print(f"   4. jenga run                        # Run the application")
    
    print(f"\n💡 Tip: Run 'jenga gen' to generate IDE project files")


# ============================================================================
# PROJECT CREATION
# ============================================================================

def create_project_interactive() -> int:
    """Interactive project creation."""
    print("\n" + "="*60)
    print("📦 JENGA PROJECT CREATION WIZARD")
    print("="*60)
    
    # Find workspace
    jenga_files = list(Path(".").glob("*.jenga"))
    if not jenga_files:
        print("❌ Error: No .jenga workspace file found in current directory")
        print("💡 Hint: Run this command from workspace root or create a workspace first")
        return 1
    
    workspace_jenga_file = jenga_files[0]
    workspace_dir = workspace_jenga_file.parent
    workspace_name = workspace_jenga_file.stem
    
    print(f"📁 Workspace: {workspace_name}")
    print(f"   Location: {workspace_dir.absolute()}")
    
    # Project name
    project_name = ask_string("📝 Project name", required=True)
    
    # Project location
    print(f"\n📂 Project Location Configuration:")
    print(f"By default, project will be created in: {workspace_dir}/{project_name}/")
    project_location = ask_string("Project subdirectory (empty for workspace root)", default=".", required=False)
    
    # Project type
    print("\n🎯 Project type:")
    project_type_keys = list(PROJECT_TYPES.keys())
    project_type_names = [PROJECT_TYPES[pt]['name'] for pt in project_type_keys]
    project_type = ask_choice("Select project type", project_type_names, default=0)
    
    # Map back to key
    for key, info in PROJECT_TYPES.items():
        if info['name'] == project_type:
            project_type = key
            break
    
    # Language configuration
    print("\n🔤 Language Configuration:")
    language_keys = list(LANGUAGES.keys())
    language_names = [LANGUAGES[lang]['name'] for lang in language_keys]
    language = ask_choice("Programming language", language_names, default=1)  # Default C++
    
    # Map back to key
    for key, info in LANGUAGES.items():
        if info['name'] == language:
            language = key
            break
    
    # Standard
    standards = LANGUAGES[language]['standards']
    default_std = LANGUAGES[language]['default_std']
    default_idx = standards.index(default_std) if default_std in standards else 0
    standard = ask_choice(f"{language} standard", standards, default=default_idx)
    
    # Namespace configuration (only for C++ and Objective-C++)
    main_namespace = ""
    sub_namespaces = []
    if language in ["C++", "Objective-C++"]:
        main_namespace, sub_namespaces = ask_namespace(project_name)
    
    # Read configurations from workspace
    configurations = ["Debug", "Release"]  # Default
    platforms = ["Windows", "Linux", "MacOS"]  # Default
    compiler_choice = "clang++"
    
    try:
        workspace_content = workspace_jenga_file.read_text(encoding='utf-8')
        
        # Parse configurations
        config_match = re.search(r'configurations\(\[(.*?)\]\)', workspace_content, re.DOTALL)
        if config_match:
            config_str = config_match.group(1)
            configurations = [c.strip().strip('"\'').strip() for c in config_str.split(',') if c.strip()]
        
        # Parse platforms
        plat_match = re.search(r'platforms\(\[(.*?)\]\)', workspace_content, re.DOTALL)
        if plat_match:
            plat_str = plat_match.group(1)
            platforms = [p.strip().strip('"\'').strip() for p in plat_str.split(',') if p.strip()]
        
        # Parse toolchain
        tc_match = re.search(r'with toolchain\("default", "([^"]+)"\)', workspace_content)
        if tc_match:
            compiler_choice = tc_match.group(1)
    
    except Exception as e:
        print(f"⚠️  Warning: Could not read workspace configuration: {e}")
    
    # Create project
    return create_project(
        name=project_name,
        project_type=project_type,
        location=project_location,
        language=language,
        standard=standard,
        main_namespace=main_namespace,
        sub_namespaces=sub_namespaces,
        platforms=platforms,
        configurations=configurations,
        compiler_choice=compiler_choice,
        workspace_dir=workspace_dir
    )


def create_project(
    name: str,
    project_type: str = "consoleapp",
    location: str = ".",
    language: str = "C++",
    standard: str = "C++17",
    main_namespace: str = "",
    sub_namespaces: List[str] = None,
    platforms: List[str] = None,
    configurations: List[str] = None,
    compiler_choice: str = "clang++",
    workspace_dir: Path = None
) -> int:
    """Create a new project in existing workspace."""
    
    if workspace_dir is None:
        # Find workspace
        jenga_files = list(Path(".").glob("*.jenga"))
        if not jenga_files:
            print("❌ Error: No .jenga workspace file found in current directory")
            print("💡 Hint: Run this command from workspace root")
            return 1
        workspace_dir = jenga_files[0].parent
    
    workspace_name = workspace_dir.name
    
    # Determine project directory
    if location == ".":
        project_dir = workspace_dir / name
        project_relative_path = name
    else:
        project_dir = workspace_dir / location / name
        project_relative_path = f"{location}/{name}"
    
    print(f"\n📦 Creating project '{name}' ({PROJECT_TYPES[project_type]['name']})...")
    print(f"   Location: {project_relative_path}/")
    print(f"   Language: {language} ({standard})")
    
    if main_namespace:
        print(f"   Namespace: {main_namespace}")
        if sub_namespaces:
            print(f"   Sub-namespaces: {', '.join(sub_namespaces)}")
    
    # Check if project already exists
    if project_dir.exists() and list(project_dir.glob(f"{name}.jenga")):
        print(f"⚠️  Warning: Project '{name}' already exists in '{project_relative_path}'")
        if not ask_yes_no("Overwrite existing files?", default=False):
            print("❌ Project creation cancelled")
            return 1
        print("   Updating existing project...")
    else:
        project_dir.mkdir(parents=True, exist_ok=True)
    
    # Default values
    if sub_namespaces is None:
        sub_namespaces = []
    if platforms is None:
        platforms = ["Windows", "Linux", "MacOS"]
    if configurations is None:
        configurations = ["Debug", "Release"]
    
    compiler_info = COMPILERS.get(compiler_choice, COMPILERS['clang++'])
    
    # Create project structure
    create_project_directory_structure(project_dir, name)
    
    # Create project .jenga file
    create_project_jenga_file(
        project_dir=project_dir,
        project_name=name,
        project_type=project_type,
        main_namespace=main_namespace,
        sub_namespaces=sub_namespaces,
        language=language,
        standard=standard,
        platforms=platforms,
        configurations=configurations,
        compiler_choice=compiler_choice,
        compiler_info=compiler_info,
        workspace_dir=workspace_dir
    )
    
    # Create source files based on language
    create_project_source_files(
        project_dir=project_dir,
        project_name=name,
        project_type=project_type,
        language=language,
        main_namespace=main_namespace,
        sub_namespaces=sub_namespaces,
        standard=standard
    )
    
    # Update workspace to include the project
    update_workspace_to_include_project(
        workspace_dir=workspace_dir,
        workspace_name=workspace_name,
        project_name=name,
        project_relative_path=project_relative_path
    )
    
    # Print summary
    print(f"\n✅ Project '{name}' created successfully!")
    print(f"\n📂 Project structure:")
    print(f"   {project_relative_path}/")
    print(f"   ├── {name}.jenga                    # Project configuration")
    print(f"   ├── src/{name}/                     # Source files")
    print(f"   ├── include/{name}/                 # Public headers")
    print(f"   ├── pch/                           # Precompiled headers")
    print(f"   ├── tests/                         # Unit tests")
    print(f"   ├── resources/                     # Resource files")
    print(f"   └── docs/                          # Documentation")
    
    print(f"\n✏️  Updated workspace: {workspace_name}.jenga")
    
    print(f"\n🚀 Next steps:")
    print(f"   jenga build --project {name}")
    
    if PROJECT_TYPES[project_type]['create_main']:
        print(f"   jenga run --project {name}")
    
    print(f"   jenga run --project {name}_Tests    # Run tests")
    
    return 0


def create_project_jenga_file(
    project_dir: Path,
    project_name: str,
    project_type: str,
    main_namespace: str = "",
    sub_namespaces: List[str] = None,
    language: str = "C++",
    standard: str = "C++17",
    platforms: List[str] = None,
    configurations: List[str] = None,
    compiler_choice: str = "clang++",
    compiler_info: Dict[str, Any] = None,
    debug_flags: List[str] = None,
    workspace_dir: Path = None
) -> None:
    """Create project .jenga file with proper configuration."""
    
    if sub_namespaces is None:
        sub_namespaces = []
    if platforms is None:
        platforms = ["Windows", "Linux", "MacOS"]
    if configurations is None:
        configurations = ["Debug", "Release"]
    if compiler_info is None:
        compiler_info = COMPILERS[compiler_choice]
    if debug_flags is None:
        debug_flags = []
    
    project_info = PROJECT_TYPES[project_type]
    
    content = get_file_header(
        filename=f"{project_name}.jenga",
        description=f"{project_name} Project Configuration",
        file_type="jenga",
        include_shebang=True
    )
    
    content += '''from Jenga.core.api import *

'''
    
    content += f'''with project("{project_name}"):
    {project_info['api_function']}
    language("{language}")
'''
    
    # Add language dialect
    if language == "C":
        content += f'''    cdialect("{standard}")
'''
    elif language == "C++":
        content += f'''    cppdialect("{standard}")
'''
    
    # Build namespace hierarchy
    namespace_path = ""
    if main_namespace:
        namespace_path = main_namespace
        if sub_namespaces:
            namespace_path += "::" + "::".join(sub_namespaces)
    
    if namespace_path:
        content += f'''    
    # Namespace
    defines(["NAMESPACE_{namespace_path.upper().replace('::', '_')}"])
'''
    
    # Source files patterns - CORRECTED: Use prj.name instead of project_name
    content += f'''    
    # Source files
    files([
        "src/%{{prj.name}}/**.cpp",
        "src/%{{prj.name}}/**.c",
        "src/%{{prj.name}}/**.cxx",
        "src/%{{prj.name}}/**.cc",
        "src/%{{prj.name}}/**.m",
        "src/%{{prj.name}}/**.mm"
    ])
    
    # Include directories
    includedirs([
        "include",
        "src"
    ])
    
    # Output directories
    targetdir("%{{wks.location}}/Build/Bin/%{{cfg.buildcfg}}")
    objdir("%{{wks.location}}/Build/Obj/%{{cfg.buildcfg}}/%{{prj.name}}")
    # targetname("%{{prj.name}}")  # Optional: override default target name
'''
    
    # Add PCH for libraries only
    if project_info['use_pch'] and language in ["C", "C++"]:
        content += '''    
    # Precompiled headers (for libraries)
    pchheader("pch/pch.h")
    pchsource("pch/pch.cpp")
    includedirs(["pch"])
    files(["pch/pch.cpp", "pch/pch.h"])
'''
    
    # Add platform-specific configurations
    content += '''    
    # Platform-specific configurations
'''
    
    for platform in platforms:
        if platform in PLATFORM_CONFIGS:
            config = PLATFORM_CONFIGS[platform]
            content += f'''    with filter("system:{platform}"):
        defines({config['defines']})
'''
            if config['links']:
                content += f'''        links({config['links']})
'''
            if platform in ["MacOS", "iOS"] and config['frameworks']:
                for framework in config['frameworks']:
                    content += f'''        framework("{framework}")
'''
            content += '''
'''
    
    # Add build configuration filters
    content += '''    # Build configurations
'''
    
    for config in configurations:
        if config == "Debug":
            content += '''    with filter("configurations:Debug"):
        defines(["DEBUG", "_DEBUG"])
        optimize("Off")
        symbols("On")
    
'''
        elif config == "Release":
            content += '''    with filter("configurations:Release"):
        defines(["NDEBUG", "RELEASE"])
        optimize("Speed")
        symbols("Off")
    
'''
        elif config == "Dist":
            content += '''    with filter("configurations:Dist"):
        defines(["NDEBUG", "DIST"])
        optimize("Full")
        symbols("Off")
    
'''
        elif config == "Profile":
            content += '''    with filter("configurations:Profile"):
        defines(["NDEBUG", "PROFILE"])
        optimize("Speed")
        symbols("On")
    
'''
        elif config == "Coverage":
            content += '''    with filter("configurations:Coverage"):
        defines(["COVERAGE"])
        optimize("Off")
        symbols("On")
    
'''
    
    # Add toolchain selection
    content += f'''    # Use workspace toolchain
    usetoolchain("default")
'''
    
    content += get_file_footer(f"{project_name}.jenga", "jenga")
    
    (project_dir / f"{project_name}.jenga").write_text(content, encoding='utf-8')
    print(f"✅ Created: {project_name}.jenga")


def update_workspace_to_include_project(
    workspace_dir: Path,
    workspace_name: str,
    project_name: str,
    project_relative_path: str
) -> None:
    """Update workspace .jenga file to include the new project."""
    
    workspace_jenga_file = workspace_dir / f"{workspace_name}.jenga"
    content = workspace_jenga_file.read_text(encoding='utf-8')
    
    # Check if already included
    include_pattern = f'addprojects("{project_relative_path}/{project_name}.jenga"'
    if include_pattern in content:
        print(f"⚠️  Project already included in workspace")
        return
    
    # Find the end of the workspace context
    lines = content.split('\n')
    insert_index = -1
    
    # Look for the last line before the footer
    for i, line in enumerate(lines):
        if line.strip().startswith('# END OF FILE:') or line.strip().startswith('// END OF FILE:'):
            insert_index = i
            break
    
    if insert_index == -1:
        # If no footer, insert at end
        insert_index = len(lines)
    
    # Prepare line to insert
    include_line = f'    addprojects("{project_relative_path}/{project_name}.jenga", ["{project_name}"])'
    
    # Insert before footer
    lines.insert(insert_index, include_line)
    lines.insert(insert_index, '')
    lines.insert(insert_index, f'    # Included project: {project_name}')
    
    workspace_jenga_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ Added project to workspace: {project_relative_path}/{project_name}.jenga")


# ============================================================================
# PROJECT SOURCE FILES CREATION
# ============================================================================

def create_project_source_files(
    project_dir: Path,
    project_name: str,
    project_type: str,
    language: str = "C++",
    main_namespace: str = "",
    sub_namespaces: List[str] = None,
    standard: str = "C++17"
) -> None:
    """Create source files for a project based on language."""
    
    if sub_namespaces is None:
        sub_namespaces = []
    
    project_info = PROJECT_TYPES[project_type]
    
    # Create main file for executable projects (without namespace)
    if project_info['create_main']:
        if language == "C":
            create_c_main_file(project_dir, project_name)
        else:  # C++, Objective-C, etc.
            create_cpp_main_file(project_dir, project_name, language)
    
    # Create test file (with namespace if applicable)
    create_test_file(project_dir, project_name, language, main_namespace, sub_namespaces)
    
    # Create precompiled header for libraries only
    if project_info['use_pch'] and language in ["C", "C++"]:
        create_precompiled_header(project_dir, project_name, language, standard)


def create_cpp_main_file(
    project_dir: Path,
    project_name: str,
    language: str = "C++"
) -> None:
    """Create main.cpp file for C++ project (without namespace)."""
    
    src_dir = project_dir / "src" / project_name
    src_dir.mkdir(parents=True, exist_ok=True)
    
    main_file = src_dir / "main.cpp"
    
    content = get_file_header(
        filename="main.cpp",
        description=f"Application entry point for {project_name}",
        file_type="cpp"
    )
    
    content += f'''#include <iostream>
#include <cstdlib>

/**
 * @brief Main function
 * @param argc Argument count
 * @param argv Argument vector
 * @return Exit code
 */
int main(int argc, char* argv[]) {{
    std::cout << "========================================" << std::endl;
    std::cout << "    {project_name} Application" << std::endl;
    std::cout << "========================================" << std::endl;
    
    std::cout << "\\nCommand line arguments:" << std::endl;
    for (int i = 0; i < argc; ++i) {{
        std::cout << "  [" << i << "] " << argv[i] << std::endl;
    }}
    
    std::cout << "\\nStarting application..." << std::endl;
    
    // TODO: Add your application logic here
    
    std::cout << "\\n{project_name} completed successfully!" << std::endl;
    return EXIT_SUCCESS;
}}
'''
    
    content += get_file_footer("main.cpp", "cpp")
    
    main_file.write_text(content, encoding='utf-8')
    print(f"✅ Created: src/{project_name}/main.cpp")


def create_c_main_file(
    project_dir: Path,
    project_name: str
) -> None:
    """Create main.c file for C project."""
    
    src_dir = project_dir / "src" / project_name
    src_dir.mkdir(parents=True, exist_ok=True)
    
    main_file = src_dir / "main.c"
    
    content = get_file_header(
        filename="main.c",
        description=f"Application entry point for {project_name} (C)",
        file_type="c"
    )
    
    content += f'''#include <stdio.h>
#include <stdlib.h>

int main(int argc, char* argv[]) {{
    printf("========================================\\n");
    printf("    {project_name} Application (C)\\n");
    printf("========================================\\n");
    
    printf("\\nCommand line arguments:\\n");
    for (int i = 0; i < argc; ++i) {{
        printf("  [%d] %s\\n", i, argv[i]);
    }}
    
    printf("\\nStarting application...\\n");
    
    // TODO: Add your application logic here
    
    printf("\\n{project_name} completed successfully!\\n");
    return EXIT_SUCCESS;
}}
'''
    
    content += get_file_footer("main.c", "c")
    
    main_file.write_text(content, encoding='utf-8')
    print(f"✅ Created: src/{project_name}/main.c")


def create_test_file(
    project_dir: Path,
    project_name: str,
    language: str = "C++",
    main_namespace: str = "",
    sub_namespaces: List[str] = None
) -> None:
    """Create test file for the project (with namespace if applicable)."""
    
    if sub_namespaces is None:
        sub_namespaces = []
    
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    if language == "C":
        test_file = tests_dir / f"test_{project_name.lower()}.c"
        
        content = get_file_header(
            filename=f"test_{project_name.lower()}.c",
            description=f"Tests for {project_name} (C)",
            file_type="c"
        )
        
        content += f'''#include <stdio.h>
#include <assert.h>

void test_example() {{
    printf("Running example test for {project_name}\\n");
    assert(1 == 1);  // Example test
    printf("✓ Example test passed\\n");
}}

int main() {{
    printf("Running tests for {project_name}\\n");
    test_example();
    printf("\\nAll tests passed!\\n");
    return 0;
}}
'''
        
        content += get_file_footer(f"test_{project_name.lower()}.c", "c")
        test_file.write_text(content, encoding='utf-8')
        
    else:  # C++ or other languages
        test_file = tests_dir / f"test_{project_name.lower()}.cpp"
        
        # Build namespace hierarchy for tests
        namespace_content = ""
        namespace_close = ""
        namespace_call = ""
        if main_namespace:
            namespace_path = main_namespace
            if sub_namespaces:
                namespace_path += "::" + "::".join(sub_namespaces)
            namespace_content = f"namespace {namespace_path} {{\n\n"
            namespace_close = f"\n}} // namespace {namespace_path}"
            namespace_call = f"{namespace_path}::"
        
        content = get_file_header(
            filename=f"test_{project_name.lower()}.cpp",
            description=f"Tests for {project_name}",
            file_type="cpp"
        )
        
        content += '''#include <iostream>
#include <cassert>

'''
        
        content += namespace_content
        
        content += f'''void test_example() {{
    std::cout << "Running example test for {project_name}" << std::endl;
    assert(1 == 1);  // Example test
    std::cout << "✓ Example test passed" << std::endl;
}}
'''
        
        content += namespace_close
        
        content += f'''

int main() {{
    std::cout << "Running tests for {project_name}" << std::endl;
    {namespace_call}test_example();
    std::cout << "\\nAll tests passed!" << std::endl;
    return 0;
}}
'''
        
        content += get_file_footer(f"test_{project_name.lower()}.cpp", "cpp")
        test_file.write_text(content, encoding='utf-8')
    
    print(f"✅ Created: tests/test_{project_name.lower()}.{'c' if language == 'C' else 'cpp'}")


def create_precompiled_header(
    project_dir: Path,
    project_name: str,
    language: str = "C++",
    standard: str = "C++17"
) -> None:
    """Create precompiled header files for libraries only."""
    
    pch_dir = project_dir / "pch"
    pch_dir.mkdir(parents=True, exist_ok=True)
    
    if language == "C":
        # C precompiled header
        pch_header = pch_dir / "pch.h"
        
        content = get_file_header("pch.h", f"Precompiled header for {project_name} (C)", "h")
        content += '''#pragma once

// Standard C headers
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include <ctype.h>
#include <assert.h>

// Platform detection
#if defined(_WIN32)
    #define PLATFORM_WINDOWS 1
    #define PLATFORM_LINUX 0
    #define PLATFORM_MACOS 0
    #define PLATFORM_ANDROID 0
    #define PLATFORM_IOS 0
#elif defined(__linux__)
    #define PLATFORM_WINDOWS 0
    #define PLATFORM_LINUX 1
    #define PLATFORM_MACOS 0
    #define PLATFORM_ANDROID 0
    #define PLATFORM_IOS 0
#elif defined(__APPLE__)
    #include <TargetConditionals.h>
    #if TARGET_OS_IPHONE
        #define PLATFORM_WINDOWS 0
        #define PLATFORM_LINUX 0
        #define PLATFORM_MACOS 0
        #define PLATFORM_ANDROID 0
        #define PLATFORM_IOS 1
    #else
        #define PLATFORM_WINDOWS 0
        #define PLATFORM_LINUX 0
        #define PLATFORM_MACOS 1
        #define PLATFORM_ANDROID 0
        #define PLATFORM_IOS 0
    #endif
#elif defined(__ANDROID__)
    #define PLATFORM_WINDOWS 0
    #define PLATFORM_LINUX 0
    #define PLATFORM_MACOS 0
    #define PLATFORM_ANDROID 1
    #define PLATFORM_IOS 0
#endif

// Common macros
#define ARRAY_SIZE(arr) (sizeof(arr) / sizeof((arr)[0]))
#define UNUSED(x) (void)(x)

// Debug macros
#ifdef DEBUG
    #define DEBUG_LOG(fmt, ...) printf("[DEBUG] " fmt "\\n", ##__VA_ARGS__)
    #define ASSERT(cond) assert(cond)
#else
    #define DEBUG_LOG(fmt, ...)
    #define ASSERT(cond)
#endif
'''
        content += get_file_footer("pch.h", "h")
        pch_header.write_text(content, encoding='utf-8')
        
        # PCH source
        pch_source = pch_dir / "pch.c"
        content = get_file_header("pch.c", f"Precompiled header implementation for {project_name} (C)", "c")
        content += '''#include "pch.h"
// Precompiled header implementation
'''
        content += get_file_footer("pch.c", "c")
        pch_source.write_text(content, encoding='utf-8')
        
    else:  # C++
        # C++ precompiled header
        pch_header = pch_dir / "pch.h"
        
        content = get_file_header("pch.h", f"Precompiled header for {project_name}", "h")
        content += '''#pragma once

// Standard C++ headers
#include <iostream>
#include <cstdlib>
#include <cstdint>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <algorithm>
#include <functional>
#include <chrono>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

// C compatibility
#include <cstdio>
#include <cstring>
#include <cmath>
#include <cassert>

// Platform detection
#if defined(_WIN32)
    #define PLATFORM_WINDOWS 1
    #define PLATFORM_LINUX 0
    #define PLATFORM_MACOS 0
    #define PLATFORM_ANDROID 0
    #define PLATFORM_IOS 0
#elif defined(__linux__)
    #define PLATFORM_WINDOWS 0
    #define PLATFORM_LINUX 1
    #define PLATFORM_MACOS 0
    #define PLATFORM_ANDROID 0
    #define PLATFORM_IOS 0
#elif defined(__APPLE__)
    #include <TargetConditionals.h>
    #if TARGET_OS_IPHONE
        #define PLATFORM_WINDOWS 0
        #define PLATFORM_LINUX 0
        #define PLATFORM_MACOS 0
        #define PLATFORM_ANDROID 0
        #define PLATFORM_IOS 1
    #else
        #define PLATFORM_WINDOWS 0
        #define PLATFORM_LINUX 0
        #define PLATFORM_MACOS 1
        #define PLATFORM_ANDROID 0
        #define PLATFORM_IOS 0
    #endif
#elif defined(__ANDROID__)
    #define PLATFORM_WINDOWS 0
    #define PLATFORM_LINUX 0
    #define PLATFORM_MACOS 0
    #define PLATFORM_ANDROID 1
    #define PLATFORM_IOS 0
#endif

// Common macros
#define ARRAY_SIZE(arr) (sizeof(arr) / sizeof((arr)[0]))
#define UNUSED(x) (void)(x)
#define NO_COPY(Class) Class(const Class&) = delete; Class& operator=(const Class&) = delete
#define NO_MOVE(Class) Class(Class&&) = delete; Class& operator=(Class&&) = delete

// Debug macros
#ifdef DEBUG
    #define DEBUG_LOG(msg) std::cout << "[DEBUG] " << msg << std::endl
    #define ASSERT(cond) assert(cond)
#else
    #define DEBUG_LOG(msg)
    #define ASSERT(cond)
#endif
'''
        content += get_file_footer("pch.h", "h")
        pch_header.write_text(content, encoding='utf-8')
        
        # PCH source
        pch_source = pch_dir / "pch.cpp"
        content = get_file_header("pch.cpp", f"Precompiled header implementation for {project_name}", "cpp")
        content += '''#include "pch.h"
// Precompiled header implementation
'''
        content += get_file_footer("pch.cpp", "cpp")
        pch_source.write_text(content, encoding='utf-8')
    
    print(f"✅ Created: pch/pch.{'h and pch.c' if language == 'C' else 'h and pch.cpp'}")


# ============================================================================
# FILE CREATION FUNCTIONS
# ============================================================================

def create_file_interactive() -> int:
    """Interactive file creation."""
    print("\n" + "="*60)
    print("📝 JENGA FILE CREATION WIZARD")
    print("="*60)
    
    # File name
    file_name = ask_string("📝 File name (without extension)", required=True)
    
    # File type
    print("\n🎯 File type:")
    file_types = [
        "class", "struct", "enum", "interface",
        "header", "source", "cpp", "c", "text"
    ]
    file_type = ask_choice("Select file type", file_types, default=0)
    
    # Project (optional)
    project = ask_string("📦 Project name (leave empty for current)", required=False)
    if not project:
        project = None
    
    # Location (optional)
    location = ask_string("📂 Location (relative to project, leave empty for default)", required=False)
    if not location:
        location = None
    
    # Namespace (for C++ files)
    namespace = None
    if file_type in ["class", "struct", "enum", "interface", "header", "cpp"]:
        use_namespace = ask_yes_no("📦 Use namespace?", default=True)
        if use_namespace:
            namespace = ask_string("Namespace (leave empty for none)", required=False)
            if not namespace:
                namespace = None
    
    # Create file
    return create_file(
        name=file_name,
        file_type=file_type,
        project=project,
        location=location,
        namespace=namespace
    )


def create_file(
    name: str,
    file_type: str = "class",
    project: str = None,
    location: str = None,
    namespace: str = None
) -> int:
    """
    Create a source file in a project.
    """
    
    # Find project
    if project is None:
        # Auto-detect project
        current_path = Path.cwd()
        
        # Look for .jenga files
        jenga_files = list(current_path.rglob("*.jenga"))
        
        if not jenga_files:
            print("❌ Error: No project found")
            print("💡 Hint: Run from project directory or specify --project")
            return 1
        
        # Find a project .jenga file
        project_dir = None
        for jenga_file in jenga_files:
            content = jenga_file.read_text()
            if "with project" in content:
                project_dir = jenga_file.parent
                break
        
        if project_dir is None:
            project_dir = jenga_files[0].parent
    else:
        # Find project by name
        project_dirs = list(Path(".").rglob(f"*/{project}"))
        if not project_dirs:
            print(f"❌ Error: Project '{project}' not found")
            return 1
        project_dir = project_dirs[0]
    
    project_name = project_dir.name
    
    print(f"\n📝 Creating {file_type} '{name}'...")
    print(f"   Project: {project_name}")
    
    # Determine target directory
    if location:
        target_dir = project_dir / location
    elif file_type in ["header", "h"]:
        target_dir = project_dir / "include" / project_name
    else:
        target_dir = project_dir / "src" / project_name
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create file based on type
    if file_type in ["class", "struct", "enum", "interface"]:
        create_cpp_composite_file(name, file_type, target_dir, project_name, namespace)
    elif file_type in ["header", "h"]:
        create_header_file_simple(name, target_dir, project_name, namespace)
    elif file_type in ["source", "cpp"]:
        create_source_file_simple(name, "cpp", target_dir, project_name, namespace)
    elif file_type == "c":
        create_source_file_simple(name, "c", target_dir, project_name, namespace)
    elif file_type == "text":
        create_text_file_simple(name, target_dir)
    else:
        print(f"❌ Unknown file type: {file_type}")
        return 1
    
    print(f"✅ File created successfully!")
    return 0


def create_cpp_composite_file(
    name: str,
    file_type: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> None:
    """Create C++ class/struct/enum files."""
    
    # Create header file
    create_cpp_header_file(name, file_type, target_dir, project_name, namespace)
    
    # Create source file for types that need it
    if file_type in ["class", "struct"]:
        create_cpp_source_file(name, file_type, target_dir, project_name, namespace)


def create_cpp_header_file(
    name: str,
    file_type: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> None:
    """Create C++ header file."""
    
    guard = f"{project_name.upper()}_{name.upper()}_H"
    header_file = target_dir / f"{name}.h"
    
    content = get_file_header(
        filename=f"{name}.h",
        description=f"{name} {file_type}",
        file_type="h"
    )
    
    content += f'''#pragma once
#ifndef {guard}
#define {guard}

'''
    
    if namespace:
        content += f'''namespace {namespace} {{
'''
    
    # Add class/struct/enum definition
    if file_type == "class":
        content += f'''
class {name} {{
public:
    {name}();
    virtual ~{name}();
    
    // TODO: Add your class methods here
    
private:
    // TODO: Add your class members here
}};
'''
    elif file_type == "struct":
        content += f'''
struct {name} {{
    // TODO: Add your struct members here
}};
'''
    elif file_type == "enum":
        content += f'''
enum class {name} {{
    None = 0,
    First,
    Second,
    // TODO: Add your enum values here
}};
'''
    elif file_type == "interface":
        content += f'''
class {name} {{
public:
    virtual ~{name}() = default;
    
    // TODO: Add your interface methods here
    
protected:
    {name}() = default;
    
private:
    // Disable copying
    {name}(const {name}&) = delete;
    {name}& operator=(const {name}&) = delete;
}};
'''
    
    if namespace:
        content += f'''
}} // namespace {namespace}
'''
    
    content += f'''
#endif // {guard}
'''
    
    content += get_file_footer(f"{name}.h", "h")
    
    header_file.write_text(content, encoding='utf-8')
    print(f"✅ Created: {header_file.relative_to(Path.cwd())}")


def create_cpp_source_file(
    name: str,
    file_type: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> None:
    """Create C++ source file."""
    
    source_file = target_dir / f"{name}.cpp"
    
    content = get_file_header(
        filename=f"{name}.cpp",
        description=f"Implementation of {name} {file_type}",
        file_type="cpp"
    )
    
    content += f'''#include "{name}.h"

'''
    
    if namespace:
        content += f'''namespace {namespace} {{
'''
    
    # Add implementation based on file type
    if file_type == "class":
        content += f'''
{name}::{name}() {{
    // Constructor implementation
}}

{name}::~{name}() {{
    // Destructor implementation
}}
'''
    elif file_type == "struct":
        content += f'''
// {name} implementation
// TODO: Add your struct implementation here
'''
    
    if namespace:
        content += f'''
}} // namespace {namespace}
'''
    
    content += get_file_footer(f"{name}.cpp", "cpp")
    
    source_file.write_text(content, encoding='utf-8')
    print(f"✅ Created: {source_file.relative_to(Path.cwd())}")


def create_header_file_simple(
    name: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> None:
    """Create simple header file."""
    
    header_file = target_dir / f"{name}.h"
    guard = f"{project_name.upper()}_{name.upper()}_H"
    
    content = get_file_header(
        filename=f"{name}.h",
        description=f"{name} header",
        file_type="h"
    )
    
    content += f'''#pragma once
#ifndef {guard}
#define {guard}

'''
    
    if namespace:
        content += f'''namespace {namespace} {{
    
    // TODO: Add your declarations here
    
}} // namespace {namespace}
'''
    else:
        content += '''// TODO: Add your declarations here
'''
    
    content += f'''
#endif // {guard}
'''
    
    content += get_file_footer(f"{name}.h", "h")
    
    header_file.write_text(content, encoding='utf-8')
    print(f"✅ Created: {header_file.relative_to(Path.cwd())}")


def create_source_file_simple(
    name: str,
    file_ext: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> None:
    """Create simple source file."""
    
    source_file = target_dir / f"{name}.{file_ext}"
    
    content = get_file_header(
        filename=f"{name}.{file_ext}",
        description=f"{name} implementation",
        file_type=file_ext
    )
    
    if file_ext == "cpp":
        content += '''#include <iostream>

'''
        if namespace:
            content += f'''namespace {namespace} {{
    
    // TODO: Add your implementation here
    
}} // namespace {namespace}
'''
        else:
            content += '''// TODO: Add your implementation here
'''
    
    elif file_ext == "c":
        content += '''#include <stdio.h>

// TODO: Add your C implementation here
'''
    
    content += get_file_footer(f"{name}.{file_ext}", file_ext)
    
    source_file.write_text(content, encoding='utf-8')
    print(f"✅ Created: {source_file.relative_to(Path.cwd())}")


def create_text_file_simple(name: str, target_dir: Path) -> None:
    """Create text file."""
    
    text_file = target_dir / f"{name}.txt"
    
    content = get_file_header(
        filename=f"{name}.txt",
        description=f"{name} text file",
        file_type="txt"
    )
    
    content += f'''{name}
========

Description:
TODO: Add your text content here.

Created with Jenga Build System v{VERSION}
'''
    
    content += get_file_footer(f"{name}.txt", "txt")
    
    text_file.write_text(content, encoding='utf-8')
    print(f"✅ Created: {text_file.relative_to(Path.cwd())}")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def execute(args):
    """Main entry point for create command."""
    
    parser = argparse.ArgumentParser(
        description="Create workspaces, projects, and files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Examples:
  jenga create workspace                  # Interactive workspace creation
  jenga create workspace MyGame           # Quick workspace with default settings
  jenga create project                    # Interactive project creation
  jenga create project Engine --type staticlib --language C
  jenga create project Tools --location utils/tools --language C++ --std C++17
  jenga create file                       # Interactive file creation
  jenga create file Player --type class
  jenga create file Config --type text --location config
  jenga create file MathUtils --type header --namespace math

Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}
Jenga Build System v{VERSION}
'''
    )
    
    subparsers = parser.add_subparsers(
        dest='subcommand',
        help='What to create',
        required=True
    )
    
    # Workspace command
    ws_parser = subparsers.add_parser(
        'workspace',
        help='Create a new workspace (interactive if no arguments)'
    )
    ws_parser.add_argument(
        'name',
        nargs='?',
        help='Workspace name (triggers quick creation)'
    )
    ws_parser.add_argument(
        '--location',
        default='.',
        help='Where to create workspace'
    )
    ws_parser.add_argument(
        '--type',
        choices=list(PROJECT_TYPES.keys()),
        default='consoleapp',
        help='Type of main project (if created)'
    )
    ws_parser.add_argument(
        '--no-project',
        action='store_true',
        help='Do not create main project'
    )
    ws_parser.add_argument(
        '--namespace',
        help='Main namespace for the project'
    )
    ws_parser.add_argument(
        '--project-name',
        help='Name of the main project (defaults to workspace name)'
    )
    ws_parser.add_argument(
        '--project-location',
        default='.',
        help='Where to create main project (relative to workspace)'
    )
    ws_parser.add_argument(
        '--compiler',
        choices=list(COMPILERS.keys()),
        default='clang++',
        help='Compiler to use for the workspace'
    )
    ws_parser.add_argument(
        '--language',
        choices=list(LANGUAGES.keys()),
        default='C++',
        help='Programming language for main project'
    )
    ws_parser.add_argument(
        '--std',
        help='Language standard (e.g., C++20, C17)'
    )
    ws_parser.add_argument(
        '--platforms',
        nargs='+',
        choices=PLATFORMS,
        help='Target platforms'
    )
    ws_parser.add_argument(
        '--architectures',
        nargs='+',
        choices=ARCHITECTURES,
        help='Target architectures'
    )
    ws_parser.add_argument(
        '--configurations',
        nargs='+',
        choices=CONFIGURATIONS,
        help='Build configurations'
    )
    
    # Project command
    proj_parser = subparsers.add_parser(
        'project',
        help='Create a new project (interactive if no arguments)'
    )
    proj_parser.add_argument(
        'name',
        nargs='?',
        help='Project name'
    )
    proj_parser.add_argument(
        '--type',
        choices=list(PROJECT_TYPES.keys()),
        default='consoleapp',
        help='Project type'
    )
    proj_parser.add_argument(
        '--location',
        default='.',
        help='Where to create project (relative to workspace)'
    )
    proj_parser.add_argument(
        '--namespace',
        help='Main namespace for the project'
    )
    proj_parser.add_argument(
        '--sub-namespaces',
        nargs='+',
        help='Sub-namespaces'
    )
    proj_parser.add_argument(
        '--language',
        choices=list(LANGUAGES.keys()),
        help='Programming language'
    )
    proj_parser.add_argument(
        '--std',
        help='Language standard (e.g., C++20, C17)'
    )
    
    # File command
    file_parser = subparsers.add_parser(
        'file',
        help='Create a source file (interactive if no arguments)'
    )
    file_parser.add_argument(
        'name',
        nargs='?',
        help='File/Class name (without extension)'
    )
    file_parser.add_argument(
        '--type',
        default='class',
        choices=['class', 'struct', 'enum', 'interface', 'header', 'source', 'cpp', 'c', 'text'],
        help='File type'
    )
    file_parser.add_argument(
        '--project',
        help='Project name (auto-detected if not specified)'
    )
    file_parser.add_argument(
        '--location',
        help='Where to create file (relative to project)'
    )
    file_parser.add_argument(
        '--namespace',
        help='Namespace for C++ files'
    )
    
    # Parse arguments
    parsed = parser.parse_args(args)
    
    # Handle commands
    if parsed.subcommand == 'workspace':
        if parsed.name:
            # Quick creation with arguments
            return create_workspace(
                workspace_name=parsed.name,
                location=parsed.location,
                create_main_project=not parsed.no_project,
                main_project_type=parsed.type,
                main_project_namespace=parsed.namespace or "",
                project_name=parsed.project_name,
                project_location=parsed.project_location,
                language=parsed.language,
                standard=parsed.std or LANGUAGES[parsed.language]['default_std'],
                platforms=parsed.platforms,
                architectures=parsed.architectures,
                configurations=parsed.configurations,
                compiler_choice=parsed.compiler
            )
        else:
            # Interactive creation
            return create_workspace_interactive()
    
    elif parsed.subcommand == 'project':
        if parsed.name:
            # Quick creation with arguments
            return create_project(
                name=parsed.name,
                project_type=parsed.type,
                location=parsed.location,
                language=parsed.language or "C++",
                standard=parsed.std or LANGUAGES[parsed.language or "C++"]['default_std'],
                main_namespace=parsed.namespace or "",
                sub_namespaces=parsed.sub_namespaces or []
            )
        else:
            # Interactive creation
            return create_project_interactive()
    
    elif parsed.subcommand == 'file':
        if parsed.name:
            # Quick creation with arguments
            return create_file(
                name=parsed.name,
                file_type=parsed.type,
                project=parsed.project,
                location=parsed.location,
                namespace=parsed.namespace
            )
        else:
            # Interactive creation
            return create_file_interactive()
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(execute(sys.argv[1:]))