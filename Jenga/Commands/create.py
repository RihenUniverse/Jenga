#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Create Command
Copyright © 2024-2026 Rihen. All rights reserved.
Proprietary License - Free to use and modify.

Create workspaces, projects, and files with professional structure.
"""

import os
import sys
import re
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# ============================================================================
# IMPORTANT: Définir les extensions reconnues comme Python
# ============================================================================

# Améliorer le chargeur pour les fichiers .jenga
class JengaLoader:
    """Chargeur pour les fichiers .jenga"""
    @classmethod
    def find_spec(cls, name, path, target=None):
        # Vérifier si le nom se termine par .jenga
        if name.endswith('.jenga') or (path and any(p.endswith('.jenga') for p in path)):
            from importlib.machinery import ModuleSpec, FileFinder
            import importlib.util
            
            # Chercher le fichier .jenga
            if path:
                for p in path:
                    jenga_path = Path(p) / name.replace('.', '/') + '.jenga'
                    if jenga_path.exists():
                        return importlib.util.spec_from_file_location(name, jenga_path)
            
            return importlib.util.spec_from_file_location(name, name.replace('.', '/') + '.jenga')
        return None
    
    @classmethod
    def create_module(cls, spec):
        return None
    
    @classmethod
    def exec_module(cls, module):
        # Lire le fichier .jenga comme un module Python
        if hasattr(module, '__file__') and module.__file__.endswith('.jenga'):
            with open(module.__file__, 'r', encoding='utf-8') as f:
                code = f.read()
            exec(code, module.__dict__)

# Ajouter .jenga comme extension Python
import importlib
sys.path_hooks.insert(0, JengaLoader)

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

# Default namespaces based on project type
DEFAULT_NAMESPACES = {
    'game': ['game', 'core', 'utils', 'graphics', 'audio', 'physics'],
    'engine': ['engine', 'core', 'render', 'math', 'input', 'platform'],
    'library': ['lib', 'core', 'utils', 'api', 'internal'],
    'app': ['app', 'core', 'ui', 'services', 'models'],
    'tool': ['tool', 'core', 'cli', 'utils', 'io'],
}

# Platform and architecture options
PLATFORMS = ["Windows", "Linux", "MacOS", "Android", "iOS", "Emscripten"]
ARCHITECTURES = ["x86", "x64", "ARM", "ARM64", "WASM"]

# Project type configurations
PROJECT_TYPES = {
    'consoleapp': {
        'name': 'Console Application',
        'template': 'consoleapp()',
        'default_language': 'C++',
        'default_std': 'C++20',
        'create_main': True,
        'output_type': 'executable',
        'is_executable': True,
    },
    'windowedapp': {
        'name': 'Windowed Application',
        'template': 'windowedapp()',
        'default_language': 'C++',
        'default_std': 'C++20',
        'create_main': True,
        'output_type': 'executable',
        'is_executable': True,
    },
    'staticlib': {
        'name': 'Static Library',
        'template': 'staticlib()',
        'default_language': 'C++',
        'default_std': 'C++20',
        'create_main': False,
        'output_type': 'library',
        'is_executable': False,
    },
    'sharedlib': {
        'name': 'Shared Library',
        'template': 'sharedlib()',
        'default_language': 'C++',
        'default_std': 'C++20',
        'create_main': False,
        'output_type': 'library',
        'is_executable': False,
    },
    'androidapp': {
        'name': 'Android Application',
        'template': 'sharedlib()',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': True,
        'output_type': 'sharedlib',
        'platforms': ['Android'],
        'is_executable': True,
    },
    'iosapp': {
        'name': 'iOS Application',
        'template': 'sharedlib()',
        'default_language': 'C++',
        'default_std': 'C++17',
        'create_main': True,
        'output_type': 'sharedlib',
        'platforms': ['iOS'],
        'is_executable': True,
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
    
    # Shebang pour les fichiers exécutables Python
    shebang = ''
    if include_shebang and file_type in ['py', 'jenga']:
        shebang = '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n\n'
    
    # Si c'est un fichier C/C++/Objective-C, utiliser le style de commentaire C
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
        # Fichiers Python et similaires
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
        # Markdown
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
        # XML
        content = f'''{comment_start}
{filename}
{description}
{'=' * 60}
Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{LICENSE_TYPE}

Generated by Jenga Build System v{VERSION}
Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{comment_end}

'''
    elif file_type == 'json':
        # JSON
        content = f'''{comment_start}
{filename}
{description}
{'=' * 60}
Copyright © {COPYRIGHT_YEAR} {COMPANY_NAME}. All rights reserved.
{LICENSE_TYPE}

Generated by Jenga Build System v{VERSION}
Creation Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{comment_end}

'''
    else:
        # Par défaut
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


def ask_namespace(default_namespace: str) -> Tuple[str, List[str]]:
    """Ask for namespace configuration."""
    print("\n📦 Namespace Configuration:")
    
    # Main namespace
    main_ns = input(f"Main namespace [{default_namespace}]: ").strip()
    if not main_ns:
        main_ns = default_namespace
    
    # Sub-namespaces
    print("\nDo you want to add sub-namespaces? (e.g., core, utils, graphics)")
    if ask_yes_no("Add sub-namespaces?", default=False):
        default_subs = DEFAULT_NAMESPACES.get(default_namespace.lower(), [])
        sub_ns = input(f"Sub-namespaces (comma separated) [{', '.join(default_subs)}]: ").strip()
        
        if sub_ns:
            sub_namespaces = [ns.strip() for ns in sub_ns.split(',')]
        else:
            sub_namespaces = default_subs
    else:
        sub_namespaces = []
    
    return main_ns, sub_namespaces


def create_directory_structure(base_path: Path, structure: List[str]) -> None:
    """Create directory structure."""
    for dir_path in structure:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  📁 Created: {dir_path}/")


# ============================================================================
# WORKSPACE CREATION
# ============================================================================

def create_workspace_interactive():
    """Interactive workspace creation with all options."""
    print("\n" + "="*60)
    print("🏗️  JENGA WORKSPACE CREATION WIZARD")
    print("="*60)
    
    # Workspace name
    workspace_name = input("\n📝 Workspace name: ").strip()
    if not workspace_name:
        print("❌ Workspace name is required")
        return 1
    
    # Location
    location = input(f"📁 Location [./]: ").strip()
    if not location:
        location = "."
    
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
    project_name = workspace_name  # Default: same as workspace
    project_location = workspace_name  # Default location for project
    
    if create_main_project:
        # ✅ CRITICAL FIX: Ask if user wants different project name
        print(f"\n📝 Project Name Configuration:")
        print(f"   By default, project name is same as workspace: {workspace_name}")
        if ask_yes_no("   Use different project name?", default=False):
            project_name = input(f"   Project name [{workspace_name}]: ").strip()
            if not project_name:
                project_name = workspace_name
        
        # ✅ CRITICAL FIX: Ask for project location
        print(f"\n📂 Project Location Configuration:")
        print(f"   Workspace: {workspace_name}")
        print(f"   Project: {project_name}")
        print(f"   By default, project will be created in: {project_name}/")
        project_location = input(f"   Where to create project? (relative to workspace) [{project_name}/]: ").strip()
        if not project_location:
            project_location = project_name
        else:
            # ✅ FIX: Ensure project location ends with project name
            if not project_location.endswith(f"/{project_name}"):
                project_location = f"{project_location}/{project_name}"
        
        # Project type
        print("\n🎯 Select main project type:")
        main_project_type = ask_choice(
            "Project type",
            list(PROJECT_TYPES.keys()),
            default=0
        )
        
        # Namespace configuration
        main_project_namespace, sub_namespaces = ask_namespace(project_name.lower())
    
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
        ["Debug", "Release", "Dist", "Profile", "Coverage"],
        defaults=["Debug", "Release"]
    )
    
    # Toolchain
    print("\n🔧 Toolchain Configuration:")
    use_custom_toolchain = ask_yes_no("Configure custom toolchain?", default=False)
    
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
        print(f"Namespace:      {main_project_namespace}")
        if sub_namespaces:
            print(f"Sub-namespaces: {', '.join(sub_namespaces)}")
    
    print(f"Platforms:      {', '.join(platforms)}")
    print(f"Architectures:  {', '.join(architectures)}")
    print(f"Configurations: {', '.join(configurations)}")
    print(f"Toolchain:      {'Custom' if use_custom_toolchain else 'Default'}")
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
        project_name=project_name if create_main_project else None,
        project_location=project_location if create_main_project else None,
        platforms=platforms,
        architectures=architectures,
        configurations=configurations,
        use_custom_toolchain=use_custom_toolchain
    )


def create_workspace(
    workspace_name: str,
    location: str = ".",
    create_main_project: bool = True,
    main_project_type: str = "consoleapp",
    main_project_namespace: str = None,
    sub_namespaces: List[str] = None,
    project_name: str = None,
    project_location: str = None,
    platforms: List[str] = None,
    architectures: List[str] = None,
    configurations: List[str] = None,
    use_custom_toolchain: bool = False
) -> int:
    """
    Create a new workspace with complete structure.
    
    Args:
        workspace_name: Name of the workspace
        location: Where to create workspace
        create_main_project: Whether to create main project
        main_project_type: Type of main project
        main_project_namespace: Main namespace for the project
        sub_namespaces: List of sub-namespaces
        project_name: Name of the main project (can be different from workspace)
        project_location: Where to create project (relative to workspace)
        platforms: Target platforms
        architectures: Target architectures
        configurations: Build configurations
        use_custom_toolchain: Whether to configure custom toolchain
    """
    
    workspace_dir = Path(location) / workspace_name
    
    if workspace_dir.exists():
        print(f"❌ Error: Directory '{workspace_dir}' already exists")
        return 1
    
    print(f"\n📁 Creating workspace '{workspace_name}'...")
    
    # Default values
    if main_project_namespace is None:
        main_project_namespace = workspace_name.lower()
    if sub_namespaces is None:
        sub_namespaces = []
    if project_name is None:
        project_name = workspace_name
    if project_location is None:
        project_location = ""
    else:
        # ✅ FIX: Ensure project location ends with project name
        if not project_location.endswith(f"/{project_name}"):
            project_location = f"{project_location}/{project_name}"
    if platforms is None:
        platforms = ["Windows", "Linux", "MacOS"]
    if architectures is None:
        architectures = ["x64"]
    if configurations is None:
        configurations = ["Debug", "Release"]
    
    # Create directory structure
    workspace_dir.mkdir(parents=True)
    
    # Main directories
    create_directory_structure(workspace_dir, [
        "assets",
        "docs",
        "externals",
        "tools",
        "scripts",
        "config",
        ".github/workflows",
    ])
    
    # Create workspace .jenga file
    create_workspace_jenga_file(
        workspace_dir=workspace_dir,
        workspace_name=workspace_name,
        platforms=platforms,
        architectures=architectures,
        configurations=configurations,
        use_custom_toolchain=use_custom_toolchain,
        create_main_project=create_main_project,
        main_project_type=main_project_type,
        project_name=project_name,
        project_location=project_location
    )
    
    # Create main project if requested
    if create_main_project:
        # ✅ CRITICAL FIX: Create project directory FIRST
        project_dir = workspace_dir / project_location
        project_dir.mkdir(parents=True, exist_ok=True)
        print(f"  📁 Created project directory: {project_location}/")
        
        # ✅ CRITICAL FIX: Create ALL project directories BEFORE creating files
        # ✅ MODIFICATION: Ajouter les sous-dossiers avec le nom du projet
        create_directory_structure(project_dir, [
            f"include/{project_name}",  # <-- MODIFICATION ICI
            f"src/{project_name}",      # <-- MODIFICATION ICI
            "pch",
            "tests",
            "resources",
            "docs",
        ])
        
        # Now create project files
        create_project_jenga_file(
            project_dir=project_dir,
            project_name=project_name,
            project_type=main_project_type,
            main_namespace=main_project_namespace,
            sub_namespaces=sub_namespaces,
            platforms=platforms,
            configurations=configurations,
            relative_path=project_location
        )
        
        # ✅ CRITICAL FIX: Create source files - directories already exist
        create_project_source_files(
            project_dir=project_dir,
            project_name=project_name,
            project_type=main_project_type,
            main_namespace=main_project_namespace,
            sub_namespaces=sub_namespaces
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
        project_location=project_location if create_main_project else None
    )
    
    # Auto-generate project files
    auto_generate_project_files(workspace_dir / f"{workspace_name}.jenga")
    
    return 0


def create_workspace_jenga_file(
    workspace_dir: Path,
    workspace_name: str,
    platforms: List[str],
    architectures: List[str],
    configurations: List[str],
    use_custom_toolchain: bool,
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
    
    # Architectures (used in toolchain configuration)
    # architectures({architectures})  # Future feature
    
'''
    
    # Décommenter startproject si c'est une application exécutable
    if create_main_project and main_project_type and PROJECT_TYPES.get(main_project_type, {}).get('is_executable', False):
        content += f'''    # Startup project
    startproject("{workspace_name}")
    
'''
    else:
        content += f'''    # Startup project (uncomment and modify)
    # startproject("{workspace_name}")
    
'''
    
    if use_custom_toolchain:
        content += '''    # Default toolchain
    with toolchain("default", "g++"):
        cppcompiler("g++")
        ccompiler("gcc")
        linker("g++")
        archiver("ar")
        
        # Common flags
        cflags(["-Wall", "-Wextra"])
        cxxflags(["-std=c++20"])
        
        # Platform-specific configurations
'''
        if "Windows" in platforms:
            content += '''        with filter("system:Windows"):
            # Windows-specific settings
            pass
        
'''
        if "Linux" in platforms:
            content += '''        with filter("system:Linux"):
            # Linux-specific settings
            pass
        
'''
        if "MacOS" in platforms:
            content += '''        with filter("system:MacOS"):
            # macOS-specific settings
            framework("Cocoa")
        
'''
    else:
        content += '''    # Toolchain will be auto-detected based on platform
'''
    
    content += '''
    # Add other projects here:
    # include("externals/mylib/mylib.jenga", ["MyLibrary"])
    # include("tools/editor/editor.jenga")
    
    # Workspace-wide settings
'''
    
    if "Android" in platforms:
        content += '''    # androidsdkpath("/path/to/android/sdk")  # For Android projects
    # androidndkpath("/path/to/android/ndk")   # For Android projects
    # javajdkpath("/path/to/java/jdk")         # For Android projects
    
'''
    
    content += f'''    # Global defines
    # defines(["WORKSPACE_{workspace_name.upper()}"])
    
    # Global dependencies (apply to all projects)
    # dependson(["Common"])
'''
    
    # Ajouter l'inclusion du projet principal si créé
    if create_main_project and project_name and project_location:
        content += f'''
    # Included project: {project_name}
    include("{project_location}/{project_name}.jenga")
'''
    
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
├── Core/                          # Core projects
│   └── {workspace_name}/          # Main project
│       ├── {workspace_name}.jenga # Project configuration
│       ├── src/                   # Source files
│       │   └── {workspace_name}/  # Project-specific source files
│       ├── include/               # Public headers
│       │   └── {workspace_name}/  # Project-specific headers
│       ├── pch/                   # Precompiled headers
│       └── tests/                 # Unit tests
├── assets/                        # Assets (images, sounds, etc.)
├── docs/                          # Documentation
├── externals/                     # External dependencies
├── tools/                         # Build tools and utilities
├── scripts/                       # Build and deployment scripts
├── config/                        # Configuration files
└── .github/workflows/             # CI/CD workflows
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
    gitignore_content = get_file_header(
        filename=".gitignore",
        description="Git ignore file",
        file_type="txt"
    )
    
    gitignore_content += '''# Jenga Build System
Build/
.cjenga/
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
'''
    
    gitignore_content += get_file_footer(".gitignore", "txt")
    (workspace_dir / ".gitignore").write_text(gitignore_content, encoding='utf-8')
    print(f"✅ Created: .gitignore")
    
    # LICENSE
    license_content = get_file_header(
        filename="LICENSE",
        description="License file",
        file_type="txt"
    )
    
    license_content += f'''{COMPANY_NAME} PROPRIETARY LICENSE

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
    
    license_content += get_file_footer("LICENSE", "txt")
    (workspace_dir / "LICENSE").write_text(license_content, encoding='utf-8')
    print(f"✅ Created: LICENSE")
    
    # Create basic docs
    (workspace_dir / "docs").mkdir(exist_ok=True)
    (workspace_dir / "docs" / "API.md").touch()
    (workspace_dir / "docs" / "ARCHITECTURE.md").touch()
    (workspace_dir / "docs" / "CONTRIBUTING.md").touch()


def print_workspace_creation_summary(
    workspace_dir: Path,
    workspace_name: str,
    create_main_project: bool,
    project_name: str = None,
    main_project_type: str = None,
    project_location: str = None
) -> None:
    """Print workspace creation summary."""
    
    print(f"\n✅ Workspace '{workspace_name}' created successfully!")
    print(f"   Location: {workspace_dir.absolute()}")
    
    print(f"\n📂 Structure created:")
    print(f"   {workspace_name}/")
    print(f"   ├── {workspace_name}.jenga          # Workspace configuration")
    
    if create_main_project and project_name and project_location:
        project_type_name = PROJECT_TYPES[main_project_type]['name']
        print(f"   ├── {project_location}/             # Main project: {project_name} ({project_type_name})")
        print(f"   │   ├── {project_name}.jenga     # Project configuration")
        print(f"   │   ├── src/{project_name}/      # Source files")
        print(f"   │   ├── include/{project_name}/  # Public headers")
        print(f"   │   ├── pch/                     # Precompiled headers")
        print(f"   │   └── tests/                   # Unit tests")
    
    print(f"   ├── assets/                        # Assets")
    print(f"   ├── docs/                          # Documentation")
    print(f"   ├── externals/                     # External dependencies")
    print(f"   ├── tools/                         # Build tools")
    print(f"   ├── scripts/                       # Scripts")
    print(f"   ├── config/                        # Configuration")
    print(f"   ├── .github/workflows/             # CI/CD")
    print(f"   ├── README.md                      # Documentation")
    print(f"   ├── .gitignore                     # Git ignore")
    print(f"   └── LICENSE                        # License")
    
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

def create_project_interactive():
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
    project_name = input("\n📝 Project name: ").strip()
    if not project_name:
        print("❌ Project name is required")
        return 1
    
    # ✅ CRITICAL: Project location - ask user
    default_location = project_name
    location = input(f"📂 Location (relative to workspace) [{default_location}/]: ").strip()
    if not location:
        location = default_location
    else:
        # ✅ FIX: Ensure location ends with project name
        if not location.endswith(f"/{project_name}"):
            location = f"{location}/{project_name}"
    
    # Project type
    print("\n🎯 Project type:")
    project_type = ask_choice(
        "Select project type",
        list(PROJECT_TYPES.keys()),
        default=0
    )
    
    # Namespace configuration
    print("\n📦 Namespace Configuration:")
    use_namespace = ask_yes_no("Use C++ namespace?", default=True)
    
    main_namespace = project_name.lower()
    sub_namespaces = []
    
    if use_namespace:
        main_namespace, sub_namespaces = ask_namespace(project_name.lower())
    
    # Get platforms from workspace
    workspace_content = workspace_jenga_file.read_text()
    platforms_match = re.search(r'platforms\(\[(.*?)\]\)', workspace_content, re.DOTALL)
    platforms = ["Windows", "Linux", "MacOS"]  # Default
    if platforms_match:
        platforms_str = platforms_match.group(1)
        platforms = [p.strip().strip('"\'') for p in platforms_str.split(',') if p.strip()]
    
    # Get configurations from workspace
    config_match = re.search(r'configurations\(\[(.*?)\]\)', workspace_content, re.DOTALL)
    configurations = ["Debug", "Release"]  # Default
    if config_match:
        config_str = config_match.group(1)
        configurations = [c.strip().strip('"\'') for c in config_str.split(',') if c.strip()]
    
    # Create project
    return create_project(
        name=project_name,
        project_type=project_type,
        location=location,
        main_namespace=main_namespace if use_namespace else None,
        sub_namespaces=sub_namespaces if use_namespace else [],
        platforms=platforms,
        configurations=configurations
    )


def create_project(
    name: str,
    project_type: str = "consoleapp",
    location: str = None,
    main_namespace: str = None,
    sub_namespaces: List[str] = None,
    platforms: List[str] = None,
    configurations: List[str] = None
) -> int:
    """
    Create a new project in existing workspace.
    
    Args:
        name: Project name
        project_type: Type of project
        location: Where to create project (relative to workspace)
        main_namespace: Main namespace for the project
        sub_namespaces: List of sub-namespaces
        platforms: Target platforms
        configurations: Build configurations
    """
    
    # Find workspace
    jenga_files = list(Path(".").glob("*.jenga"))
    if not jenga_files:
        print("❌ Error: No .jenga workspace file found in current directory")
        print("💡 Hint: Run this command from workspace root")
        return 1
    
    workspace_jenga_file = jenga_files[0]
    workspace_dir = workspace_jenga_file.parent
    
    # Determine project location
    if location is None or location == ".":
        location = ""
    else:
        # ✅ FIX: Ensure location ends with project name
        if not location.endswith(f"/{name}"):
            location = f"{location}/{name}"
    
    project_path = workspace_dir / location if location else workspace_dir / name
    project_relative_path = location if location else name
    
    print(f"\n📦 Creating project '{name}' ({PROJECT_TYPES[project_type]['name']})...")
    print(f"   Location: {project_relative_path}/")
    
    if main_namespace:
        print(f"   Namespace: {main_namespace}")
        if sub_namespaces:
            print(f"   Sub-namespaces: {', '.join(sub_namespaces)}")
    
    # Check if project already exists
    if project_path.exists():
        print(f"⚠️  Warning: Directory '{project_relative_path}' already exists")
        if not ask_yes_no("Overwrite existing files?", default=False):
            print("❌ Project creation cancelled")
            return 1
        print("   Updating existing project...")
    else:
        project_path.mkdir(parents=True, exist_ok=True)
    
    # ✅ CRITICAL FIX: Create ALL directories BEFORE creating any files
    # ✅ MODIFICATION: Ajouter les sous-dossiers avec le nom du projet
    create_directory_structure(project_path, [
        f"include/{name}",  # <-- MODIFICATION ICI
        f"src/{name}",      # <-- MODIFICATION ICI
        "pch",
        "tests",
        "resources",
        "docs",
    ])
    
    # Create project .jenga file
    create_project_jenga_file(
        project_dir=project_path,
        project_name=name,
        project_type=project_type,
        main_namespace=main_namespace,
        sub_namespaces=sub_namespaces,
        platforms=platforms,
        configurations=configurations,
        relative_path=project_relative_path
    )
    
    # ✅ CRITICAL FIX: Create source files - directories already exist
    create_project_source_files(
        project_dir=project_path,
        project_name=name,
        project_type=project_type,
        main_namespace=main_namespace,
        sub_namespaces=sub_namespaces
    )
    
    # Update workspace to include the project
    update_workspace_to_include_project(
        workspace_jenga_file=workspace_jenga_file,
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
    
    print(f"\n✏️  Updated workspace: {workspace_jenga_file.name}")
    
    print(f"\n🚀 Next steps:")
    print(f"   jenga build --project {name}")
    
    if PROJECT_TYPES[project_type]['create_main']:
        print(f"   jenga run --project {name}")
    
    print(f"   jenga run --project {name}_Tests    # Run tests")
    
    # Auto-generate project files
    auto_generate_project_files(workspace_jenga_file)
    
    return 0


def create_project_jenga_file(
    project_dir: Path,
    project_name: str,
    project_type: str,
    main_namespace: str = None,
    sub_namespaces: List[str] = None,
    platforms: List[str] = None,
    configurations: List[str] = None,
    relative_path: str = ""
) -> None:
    """Create project .jenga file."""
    
    if sub_namespaces is None:
        sub_namespaces = []
    if platforms is None:
        platforms = ["Windows", "Linux", "MacOS"]
    if configurations is None:
        configurations = ["Debug", "Release"]
    
    project_info = PROJECT_TYPES[project_type]
    
    content = get_file_header(
        filename=f"{project_name}.jenga",
        description=f"{project_name} Project Configuration",
        file_type="jenga",
        include_shebang=True
    )
    
    content += '''from Jenga.core.api import *

'''
    
    content += f'''# {project_name} - {project_info['name']}
# This project can be used standalone or included in a workspace

with workspace("{project_name}"):
    # Main project
    with project("{project_name}"):
        {project_info['template']}
        language("{project_info['default_language']}")
        cppdialect("{project_info['default_std']}")
        
        # Project location (relative to this file)
        location(".")
        
        # Source files
        files([
            "src/**/*.cpp",
            "src/**/*.c",
            "src/**/*.inl",
            "src/**/*.m",
            "src/**/*.mm",
        ])
        
        # Include directories
        includedirs([
            "include",
            "include/{project_name}",
            "src",
            "src/{project_name}"
        ])
        
        # Output directories
        targetdir("%{{wks.location}}/Build/Bin/%{{cfg.buildcfg}}")
        objdir("%{{wks.location}}/Build/Obj/%{{cfg.buildcfg}}/%{{prj.name}}")
        
        # Target name
        targetname("{project_name}")
'''
    
    # Add namespace defines if specified
    if main_namespace:
        namespace_defines = [f"PROJECT_NAMESPACE={main_namespace}"]
        
        # Add define for main namespace
        content += f'''
        # Namespace configuration
        defines(["PROJECT_NAMESPACE={main_namespace}"])
'''
        
        # Add defines for sub-namespaces
        for sub_ns in sub_namespaces:
            namespace_defines.append(f"NAMESPACE_{sub_ns.upper()}")
        
        if len(namespace_defines) > 1:
            content += f'''        defines({namespace_defines})
'''
    
    # Add project type specific configurations
    if project_type in ["androidapp", "iosapp"]:
        content += f'''
        # Mobile platform configuration
        androidapplicationid("com.{main_namespace or project_name.lower()}.app")
        androidversioncode(1)
        androidversionname("1.0.0")
        androidminsdk(21)
        androidtargetsdk(33)
'''
    
    # Add test configuration
    content += f'''
        # Unit tests
        with test("Unit"):
            testfiles(["tests/**.cpp", "tests/**.c"])
            testoptions(["--verbose", "--parallel"])
'''
    
    # ✅ CORRECTION: Ajouter les configurations build de manière conditionnelle
    content += '''
        # Build configurations
'''
    
    if "Debug" in configurations:
        content += '''        with filter("configurations:Debug"):
            defines(["DEBUG", "_DEBUG"])
            optimize("Off")
            symbols("On")
        
'''
    
    if "Release" in configurations:
        content += '''        with filter("configurations:Release"):
            defines(["NDEBUG", "RELEASE"])
            optimize("Speed")
            symbols("Off")
        
'''
    
    if "Dist" in configurations:
        content += '''        with filter("configurations:Dist"):
            defines(["NDEBUG", "DIST"])
            optimize("Full")
            symbols("Off")
        
'''
    
    if "Profile" in configurations:
        content += '''        with filter("configurations:Profile"):
            defines(["NDEBUG", "PROFILE"])
            optimize("On")
            symbols("On")
            debuginfo("Embedded")
        
'''
    
    if "Coverage" in configurations:
        content += '''        with filter("configurations:Coverage"):
            defines(["NDEBUG", "COVERAGE"])
            optimize("Off")
            symbols("On")
            debuginfo("Full")
            cxxflags(["--coverage"])
            links(["gcov"])
        
'''
    
    # ✅ CORRECTION: Ajouter les configurations platform-specific de manière conditionnelle
    content += '''
        # Platform-specific configurations
'''
    
    if "Windows" in platforms:
        content += '''        with filter("system:Windows"):
            defines(["_WIN32", "WIN32_LEAN_AND_MEAN", "WINDOWS"])
            cxxflags(["/EHsc", "/W4"])
            links(["kernel32", "user32", "gdi32", "winspool", "comdlg32", "advapi32", "shell32", "ole32", "oleaut32", "uuid", "odbc32", "odbccp32"])
            
'''
        if "Debug" in configurations:
            content += '''            with filter("configurations:Debug"):
                defines(["_DEBUG"])
                cxxflags(["/MTd"])
            
'''
        release_configs = [c for c in configurations if c in ["Release", "Dist"]]
        if release_configs:
            config_filter = " or ".join([f'configurations:{c}' for c in release_configs])
            content += f'''            with filter("{config_filter}"):
                defines(["_RELEASE"])
                cxxflags(["/MT", "/O2", "/Ob2", "/GL"])
                ldflags(["/LTCG"])
            
'''
    
    if "Linux" in platforms:
        content += '''        with filter("system:Linux"):
            defines(["_LINUX", "__linux__", "LINUX"])
            cxxflags(["-pthread"])
            links(["pthread", "dl", "m", "rt"])
            
'''
        if "Debug" in configurations:
            content += '''            with filter("configurations:Debug"):
                cxxflags(["-g3", "-Og"])
            
'''
        release_configs = [c for c in configurations if c in ["Release", "Dist"]]
        if release_configs:
            config_filter = " or ".join([f'configurations:{c}' for c in release_configs])
            content += f'''            with filter("{config_filter}"):
                cxxflags(["-O3", "-flto"])
                ldflags(["-flto"])
            
'''
    
    if "MacOS" in platforms:
        content += '''        with filter("system:MacOS"):
            defines(["_MACOS", "__APPLE__", "MACOS"])
            framework("Cocoa")
            framework("Foundation")
            framework("CoreFoundation")
            framework("CoreGraphics")
            framework("CoreServices")
            framework("Security")
            framework("SystemConfiguration")
            
'''
        if "Debug" in configurations:
            content += '''            with filter("configurations:Debug"):
                cxxflags(["-g"])
            
'''
        release_configs = [c for c in configurations if c in ["Release", "Dist"]]
        if release_configs:
            config_filter = " or ".join([f'configurations:{c}' for c in release_configs])
            content += f'''            with filter("{config_filter}"):
                cxxflags(["-O3"])
            
'''
    
    if "Android" in platforms:
        content += '''        with filter("system:Android"):
            defines(["_ANDROID", "__ANDROID__", "ANDROID"])
            links(["log", "android", "EGL", "GLESv3", "GLESv2", "OpenSLES"])
            
'''
        if "Debug" in configurations:
            content += '''            with filter("configurations:Debug"):
                cxxflags(["-g"])
            
'''
        release_configs = [c for c in configurations if c in ["Release", "Dist"]]
        if release_configs:
            config_filter = " or ".join([f'configurations:{c}' for c in release_configs])
            content += f'''            with filter("{config_filter}"):
                cxxflags(["-O3"])
            
'''
    
    if "iOS" in platforms:
        content += '''        with filter("system:iOS"):
            defines(["_IOS", "__IOS__", "IOS"])
            framework("UIKit")
            framework("Foundation")
            framework("CoreGraphics")
            framework("QuartzCore")
            framework("CoreFoundation")
            framework("Security")
            framework("SystemConfiguration")
            
'''
        if "Debug" in configurations:
            content += '''            with filter("configurations:Debug"):
                cxxflags(["-g"])
            
'''
        release_configs = [c for c in configurations if c in ["Release", "Dist"]]
        if release_configs:
            config_filter = " or ".join([f'configurations:{c}' for c in release_configs])
            content += f'''            with filter("{config_filter}"):
                cxxflags(["-O3"])
            
'''
    
    if "Emscripten" in platforms:
        content += '''        with filter("system:Emscripten"):
            defines(["_EMSCRIPTEN", "__EMSCRIPTEN__", "EMSCRIPTEN"])
            cxxflags(["-s USE_WEBGL2=1", "-s USE_SDL=2", "-s FULL_ES3=1"])
            links(["GL", "SDL2"])
            
'''
        if "Debug" in configurations:
            content += '''            with filter("configurations:Debug"):
                cxxflags(["-g4", "-s ASSERTIONS=2"])
            
'''
        if "Release" in configurations:
            content += '''            with filter("configurations:Release"):
                cxxflags(["-O2", "-s ASSERTIONS=0"])
            
'''
        if "Dist" in configurations:
            content += '''            with filter("configurations:Dist"):
                cxxflags(["-O3", "-s ASSERTIONS=0"])
            
'''
    
    content += get_file_footer(f"{project_name}.jenga", "jenga")
    
    (project_dir / f"{project_name}.jenga").write_text(content, encoding='utf-8')
    print(f"✅ Created: {project_name}.jenga")


def create_project_source_files(
    project_dir: Path,
    project_name: str,
    project_type: str,
    main_namespace: str = None,
    sub_namespaces: List[str] = None
) -> None:
    """Create source files for a project."""
    
    if sub_namespaces is None:
        sub_namespaces = []
    
    project_info = PROJECT_TYPES[project_type]
    
    # Create main header file
    create_main_header_file(project_dir, project_name, main_namespace, sub_namespaces)
    
    # Create main source file
    create_main_source_file(project_dir, project_name, main_namespace, sub_namespaces)
    
    # Create main.cpp for applications
    if project_info['create_main']:
        create_main_app_file(project_dir, project_name, main_namespace)
    
    # Create test file
    create_test_file(project_dir, project_name, main_namespace, sub_namespaces)
    
    # Create precompiled header if needed
    create_precompiled_header(project_dir, project_name)


def create_main_header_file(
    project_dir: Path,
    project_name: str,
    main_namespace: str = None,
    sub_namespaces: List[str] = None
) -> None:
    """Create main header file with namespace configuration."""
    
    if sub_namespaces is None:
        sub_namespaces = []
    
    # ✅ MODIFICATION: Créer le dossier spécifique au projet
    include_project_dir = project_dir / "include" / project_name
    include_project_dir.mkdir(parents=True, exist_ok=True)
    
    header_file = include_project_dir / f"{project_name}.h"
    guard = f"{project_name.upper()}_{project_name.upper()}_H"
    
    content = get_file_header(
        filename=f"{project_name}.h",
        description=f"Main header for {project_name}",
        file_type="h"
    )
    
    content += f'''#pragma once
#ifndef {guard}
#define {guard}

#include <string>
#include <memory>
#include <cstdint>

'''
    
    # Generate namespace declarations
    if main_namespace:
        # Main namespace
        content += f'''namespace {main_namespace} {{
'''
        
        # Sub-namespaces (nested or separate based on preference)
        if sub_namespaces:
            content += "    // Sub-namespaces\n"
            for sub_ns in sub_namespaces:
                content += f'''    namespace {sub_ns} {{
        // {sub_ns} functionality
    }}
'''
            content += "\n"
        
        content += f'''    /**
     * @class {project_name}
     * @brief Main class for {project_name}
     */
    class {project_name} {{
    public:
        /**
         * @brief Constructor
         */
        {project_name}();
        
        /**
         * @brief Destructor
         */
        virtual ~{project_name}();
        
        /**
         * @brief Initialize the {project_name}
         * @return True if successful
         */
        bool initialize();
        
        /**
         * @brief Get the version string
         * @return Version string
         */
        static std::string version();
        
        /**
         * @brief Run the main logic
         */
        void run();
        
    private:
        class Impl;
        std::unique_ptr<Impl> m_impl;
    }};
    
}} // namespace {main_namespace}
'''
    else:
        # No namespace
        content += f'''/**
 * @class {project_name}
 * @brief Main class for {project_name}
 */
class {project_name} {{
public:
    /**
     * @brief Constructor
     */
    {project_name}();
    
    /**
     * @brief Destructor
     */
    virtual ~{project_name}();
    
    /**
     * @brief Initialize the {project_name}
     * @return True if successful
     */
    bool initialize();
    
    /**
     * @brief Get the version string
     * @return Version string
     */
    static std::string version();
    
    /**
     * @brief Run the main logic
     */
    void run();
    
private:
    class Impl;
    std::unique_ptr<Impl> m_impl;
}};
'''
    
    content += f'''
#endif // {guard}
'''
    
    content += get_file_footer(f"{project_name}.h", "h")
    
    # ✅ CRITICAL: Write file safely with UTF-8 encoding
    try:
        header_file.write_text(content, encoding='utf-8')
        print(f"✅ Created: include/{project_name}/{project_name}.h")
    except Exception as e:
        print(f"❌ Error creating header file: {e}")
        # Try to create parent directory and retry
        header_file.parent.mkdir(parents=True, exist_ok=True)
        header_file.write_text(content, encoding='utf-8')
        print(f"✅ Created (retry): include/{project_name}/{project_name}.h")


def create_main_source_file(
    project_dir: Path,
    project_name: str,
    main_namespace: str = None,
    sub_namespaces: List[str] = None
) -> None:
    """Create main source file."""
    
    if sub_namespaces is None:
        sub_namespaces = []
    
    # ✅ MODIFICATION: Créer le dossier spécifique au projet
    src_project_dir = project_dir / "src" / project_name
    src_project_dir.mkdir(parents=True, exist_ok=True)
    
    source_file = src_project_dir / f"{project_name}.cpp"
    
    content = get_file_header(
        filename=f"{project_name}.cpp",
        description=f"Main implementation for {project_name}",
        file_type="cpp"
    )
    
    content += f'''#include "{project_name}/{project_name}.h"
#include <iostream>
#include <chrono>

'''
    
    if main_namespace:
        # Opening namespace
        content += f'''namespace {main_namespace} {{
'''
        
        # Nested namespaces for implementation
        nested_ns = "::".join([main_namespace] + sub_namespaces) if sub_namespaces else main_namespace
        
        content += f'''
    // PImpl pattern
    class {project_name}::Impl {{
    public:
        Impl() = default;
        ~Impl() = default;
        
        void initialize() {{
            std::cout << "{project_name} initialized" << std::endl;
            std::cout << "Namespace: {nested_ns}" << std::endl;
        }}
        
        void run() {{
            auto start = std::chrono::high_resolution_clock::now();
            std::cout << "{project_name} is running..." << std::endl;
            auto end = std::chrono::high_resolution_clock::now();
            auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
            std::cout << "Execution time: " << duration.count() << " microseconds" << std::endl;
        }}
    }};
    
    // {project_name} implementation
    {project_name}::{project_name}() : m_impl(std::make_unique<Impl>()) {{
        // Constructor
    }}
    
    {project_name}::~{project_name}() = default;
    
    bool {project_name}::initialize() {{
        m_impl->initialize();
        return true;
    }}
    
    std::string {project_name}::version() {{
        return "{VERSION}";
    }}
    
    void {project_name}::run() {{
        m_impl->run();
    }}
    
}} // namespace {main_namespace}
'''
    else:
        # No namespace
        content += f'''// PImpl pattern
class {project_name}::Impl {{
public:
    Impl() = default;
    ~Impl() = default;
    
    void initialize() {{
        std::cout << "{project_name} initialized" << std::endl;
    }}
    
    void run() {{
        auto start = std::chrono::high_resolution_clock::now();
        std::cout << "{project_name} is running..." << std::endl;
        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
        std::cout << "Execution time: " << duration.count() << " microseconds" << std::endl;
    }}
}};

// {project_name} implementation
{project_name}::{project_name}() : m_impl(std::make_unique<Impl>()) {{
    // Constructor
}}

{project_name}::~{project_name}() = default;

bool {project_name}::initialize() {{
    m_impl->initialize();
    return true;
}}

std::string {project_name}::version() {{
    return "{VERSION}";
}}

void {project_name}::run() {{
    m_impl->run();
}}
'''
    
    content += get_file_footer(f"{project_name}.cpp", "cpp")
    
    # ✅ CRITICAL: Write file safely with UTF-8 encoding
    try:
        source_file.write_text(content, encoding='utf-8')
        print(f"✅ Created: src/{project_name}/{project_name}.cpp")
    except Exception as e:
        print(f"❌ Error creating source file: {e}")
        # Try to create parent directory and retry
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text(content, encoding='utf-8')
        print(f"✅ Created (retry): src/{project_name}/{project_name}.cpp")


def create_main_app_file(project_dir: Path, project_name: str, main_namespace: str = None) -> None:
    """Create main application file."""
    
    # ✅ MODIFICATION: Créer le dossier spécifique au projet
    src_project_dir = project_dir / "src" / project_name
    src_project_dir.mkdir(parents=True, exist_ok=True)
    
    main_file = src_project_dir / "main.cpp"
    
    content = get_file_header(
        filename="main.cpp",
        description=f"Application entry point for {project_name}",
        file_type="cpp"
    )
    
    content += f'''#include <iostream>
#include <cstdlib>
'''
    
    if main_namespace:
        content += f'''#include "{project_name}/{project_name}.h"

using namespace {main_namespace};

int main(int argc, char* argv[]) {{
    std::cout << "========================================" << std::endl;
    std::cout << "    {project_name} Application" << std::endl;
    std::cout << "    Namespace: {main_namespace}" << std::endl;
    std::cout << "========================================" << std::endl;
    
    std::cout << "\\nCommand line arguments:" << std::endl;
    for (int i = 0; i < argc; ++i) {{
        std::cout << "  [" << i << "] " << argv[i] << std::endl;
    }}
    
    std::cout << "\\nInitializing {project_name}..." << std::endl;
    {project_name} app;
    
    if (!app.initialize()) {{
        std::cerr << "Failed to initialize {project_name}" << std::endl;
        return EXIT_FAILURE;
    }}
    
    std::cout << "{project_name} initialized successfully!" << std::endl;
    std::cout << "   Version: " << app.version() << std::endl;
    
    std::cout << "\\nRunning {project_name}..." << std::endl;
    app.run();
    
    std::cout << "\\n{project_name} completed successfully!" << std::endl;
    return EXIT_SUCCESS;
}}
'''
    else:
        content += f'''#include "{project_name}/{project_name}.h"

int main(int argc, char* argv[]) {{
    std::cout << "========================================" << std::endl;
    std::cout << "    {project_name} Application" << std::endl;
    std::cout << "========================================" << std::endl;
    
    std::cout << "\\nCommand line arguments:" << std::endl;
    for (int i = 0; i < argc; ++i) {{
        std::cout << "  [" << i << "] " << argv[i] << std::endl;
    }}
    
    std::cout << "\\nInitializing {project_name}..." << std::endl;
    {project_name} app;
    
    if (!app.initialize()) {{
        std::cerr << "Failed to initialize {project_name}" << std::endl;
        return EXIT_FAILURE;
    }}
    
    std::cout << "{project_name} initialized successfully!" << std::endl;
    std::cout << "   Version: " << app.version() << std::endl;
    
    std::cout << "\\nRunning {project_name}..." << std::endl;
    app.run();
    
    std::cout << "\\n{project_name} completed successfully!" << std::endl;
    return EXIT_SUCCESS;
}}
'''
    
    content += get_file_footer("main.cpp", "cpp")
    
    # ✅ CRITICAL: Write file safely with UTF-8 encoding
    try:
        main_file.write_text(content, encoding='utf-8')
        print(f"✅ Created: src/{project_name}/main.cpp")
    except Exception as e:
        print(f"❌ Error creating main file: {e}")
        # Try to create parent directory and retry
        main_file.parent.mkdir(parents=True, exist_ok=True)
        main_file.write_text(content, encoding='utf-8')
        print(f"✅ Created (retry): src/{project_name}/main.cpp")


def create_test_file(
    project_dir: Path,
    project_name: str,
    main_namespace: str = None,
    sub_namespaces: List[str] = None
) -> None:
    """Create test file."""
    
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)  # ✅ Ensure directory exists
    
    test_file = tests_dir / f"test_{project_name.lower()}.cpp"
    
    content = get_file_header(
        filename=f"test_{project_name.lower()}.cpp",
        description=f"Unit tests for {project_name}",
        file_type="cpp"
    )
    
    content += f'''#include <cassert>
#include <iostream>
'''
    
    if main_namespace:
        content += f'''#include "{project_name}/{project_name}.h"

using namespace {main_namespace};

void test_{project_name.lower()}_creation() {{
    {project_name} app;
    assert(app.initialize());
    std::cout << "test_{project_name.lower()}_creation passed" << std::endl;
}}

void test_{project_name.lower()}_version() {{
    std::string version = {project_name}::version();
    assert(!version.empty());
    std::cout << "test_{project_name.lower()}_version passed (version: " << version << ")" << std::endl;
}}

void test_{project_name.lower()}_namespace() {{
    std::cout << "test_{project_name.lower()}_namespace passed (namespace: {main_namespace})" << std::endl;
}}

int main() {{
    std::cout << "========================================" << std::endl;
    std::cout << "    Running {project_name} Tests" << std::endl;
    std::cout << "    Namespace: {main_namespace}" << std::endl;
    std::cout << "========================================" << std::endl;
    
    test_{project_name.lower()}_creation();
    test_{project_name.lower()}_version();
    test_{project_name.lower()}_namespace();
    
    std::cout << "\\n========================================" << std::endl;
    std::cout << "    ALL TESTS PASSED!" << std::endl;
    std::cout << "========================================" << std::endl;
    
    return 0;
}}
'''
    else:
        content += f'''#include "{project_name}/{project_name}.h"

void test_{project_name.lower()}_creation() {{
    {project_name} app;
    assert(app.initialize());
    std::cout << "test_{project_name.lower()}_creation passed" << std::endl;
}}

void test_{project_name.lower()}_version() {{
    std::string version = {project_name}::version();
    assert(!version.empty());
    std::cout << "test_{project_name.lower()}_version passed (version: " << version << ")" << std::endl;
}}

int main() {{
    std::cout << "========================================" << std::endl;
    std::cout << "    Running {project_name} Tests" << std::endl;
    std::cout << "========================================" << std::endl;
    
    test_{project_name.lower()}_creation();
    test_{project_name.lower()}_version();
    
    std::cout << "\\n========================================" << std::endl;
    std::cout << "    ALL TESTS PASSED!" << std::endl;
    std::cout << "========================================" << std::endl;
    
    return 0;
}}
'''
    
    content += get_file_footer(f"test_{project_name.lower()}.cpp", "cpp")
    
    # ✅ CRITICAL: Write file safely with UTF-8 encoding
    try:
        test_file.write_text(content, encoding='utf-8')
        print(f"✅ Created: tests/test_{project_name.lower()}.cpp")
    except Exception as e:
        print(f"❌ Error creating test file: {e}")
        # Try to create parent directory and retry
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(content, encoding='utf-8')
        print(f"✅ Created (retry): tests/test_{project_name.lower()}.cpp")


def create_precompiled_header(project_dir: Path, project_name: str) -> None:
    """Create precompiled header files."""
    
    pch_dir = project_dir / "pch"
    pch_dir.mkdir(parents=True, exist_ok=True)  # ✅ Ensure directory exists
    
    # PCH header
    pch_header = project_dir / "pch" / "pch.h"
    
    content = get_file_header(
        filename="pch.h",
        description=f"Precompiled header for {project_name}",
        file_type="h"
    )
    
    content += '''#pragma once

// Standard library headers
#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <set>
#include <memory>
#include <algorithm>
#include <functional>
#include <chrono>
#include <thread>
#include <mutex>
#include <atomic>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <cstdint>
#include <cassert>
#include <cstdlib>
#include <ctime>

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
#elif defined(__APPLE__) && defined(__MACH__)
    #include <TargetConditionals.h>
    #if TARGET_IPHONE_SIMULator == 1 || TARGET_OS_IPHONE == 1
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
#else
    #error "Unknown platform"
#endif

// Common macros
#define DISABLE_COPY(Class) \
    Class(const Class&) = delete; \
    Class& operator=(const Class&) = delete

#define DISABLE_MOVE(Class) \
    Class(Class&&) = delete; \
    Class& operator=(Class&&) = delete

#define DISABLE_COPY_AND_MOVE(Class) \
    DISABLE_COPY(Class); \
    DISABLE_MOVE(Class)

// Utility macros
#define ARRAY_SIZE(arr) (sizeof(arr) / sizeof((arr)[0]))
#define UNUSED(x) (void)(x)

// Logging macros (basic)
#if defined(DEBUG) || defined(_DEBUG)
    #define LOG_DEBUG(msg) std::cout << "[DEBUG] " << msg << std::endl
    #define LOG_INFO(msg) std::cout << "[INFO] " << msg << std::endl
    #define LOG_WARNING(msg) std::cout << "[WARNING] " << msg << std::endl
    #define LOG_ERROR(msg) std::cerr << "[ERROR] " << msg << std::endl
#else
    #define LOG_DEBUG(msg)
    #define LOG_INFO(msg)
    #define LOG_WARNING(msg)
    #define LOG_ERROR(msg) std::cerr << "[ERROR] " << msg << std::endl
#endif
'''
    
    content += get_file_footer("pch.h", "h")
    
    # ✅ CRITICAL: Write file safely with UTF-8 encoding
    try:
        pch_header.write_text(content, encoding='utf-8')
        print(f"✅ Created: pch/pch.h")
    except Exception as e:
        print(f"❌ Error creating PCH header: {e}")
        # Try to create parent directory and retry
        pch_header.parent.mkdir(parents=True, exist_ok=True)
        pch_header.write_text(content, encoding='utf-8')
        print(f"✅ Created (retry): pch/pch.h")
    
    # PCH source
    pch_source = project_dir / "pch" / "pch.cpp"
    pch_content = get_file_header(
        filename="pch.cpp",
        description=f"Precompiled header implementation for {project_name}",
        file_type="cpp"
    )
    pch_content += '''#include "pch.h"
// Precompiled header implementation file
'''
    pch_content += get_file_footer("pch.cpp", "cpp")
    pch_source.write_text(pch_content, encoding='utf-8')
    print(f"✅ Created: pch/pch.cpp")


def update_workspace_to_include_project(
    workspace_jenga_file: Path,
    project_name: str,
    project_relative_path: str
) -> None:
    """Update workspace .jenga file to include the new project."""
    
    content = workspace_jenga_file.read_text(encoding='utf-8')
    
    # Check if already included
    include_pattern = f'include("{project_relative_path}/{project_name}.jenga")'
    if include_pattern in content:
        print(f"⚠️  Project already included in workspace")
        return
    
    # Trouver la position pour insérer avant le footer
    lines = content.split('\n')
    
    # Chercher la ligne "# END OF FILE:"
    insert_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('# END OF FILE:') or line.strip().startswith('// END OF FILE:') or line.strip().startswith('<!-- END OF FILE:'):
            insert_index = i
            break
    
    if insert_index == -1:
        # Si pas de footer, insérer à la fin
        insert_index = len(lines)
    
    # Préparer les lignes à insérer
    include_line = f'    include("{project_relative_path}/{project_name}.jenga")'
    comment_line = f'    # Included project: {project_name}'
    
    # Insérer une ligne vide, le commentaire, puis l'include
    lines.insert(insert_index, "")
    lines.insert(insert_index, include_line)
    lines.insert(insert_index, comment_line)
    
    workspace_jenga_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f"✅ Added project to workspace: {project_relative_path}/{project_name}.jenga")


# ============================================================================
# FILE CREATION
# ============================================================================

def create_file_interactive():
    """Interactive file creation."""
    print("\n" + "="*60)
    print("📝 JENGA FILE CREATION WIZARD")
    print("="*60)
    
    # File name
    file_name = input("\n📝 File name (without extension): ").strip()
    if not file_name:
        print("❌ File name is required")
        return 1
    
    # File type
    print("\n🎯 File type:")
    file_type = ask_choice(
        "Select file type",
        [
            "class", "struct", "enum", "union", "interface",
            "header", "source", "cpp", "c", "m", "mm", "inl", "text"
        ],
        default=0
    )
    
    # Project (optional)
    project = input("\n📦 Project name (leave empty for current): ").strip()
    
    # Location (optional)
    location = input("\n📂 Location (relative to project, leave empty for default): ").strip()
    
    # Namespace (for C++ files)
    namespace = None
    if file_type in ["class", "struct", "enum", "union", "interface", "header", "cpp", "c"]:
        use_namespace = ask_yes_no("\n📦 Use namespace?", default=True)
        if use_namespace:
            namespace = input("   Namespace (leave empty for none): ").strip()
            if not namespace:
                namespace = None
    
    # Create file
    return create_file(
        name=file_name,
        file_type=file_type,
        project=project if project else None,
        location=location if location else None,
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
    
    Args:
        name: File name (without extension)
        file_type: Type of file
        project: Project name (auto-detected if None)
        location: Where to create file (relative to project)
        namespace: Namespace for C++ files
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
        
        # Find a project .jenga file (not workspace)
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
    
    print(f"\n📝 Creating {file_type} '{name}'...")
    print(f"   Project: {project_dir.name}")
    
    # Determine file extension and target directory
    file_ext, target_dir = determine_file_location(file_type, project_dir, location)
    
    # Create the file
    full_path = create_file_by_type(
        name=name,
        file_type=file_type,
        file_ext=file_ext,
        target_dir=target_dir,
        project_name=project_dir.name,
        namespace=namespace
    )
    
    if full_path:
        print(f"\n✅ File created: {full_path.relative_to(Path.cwd())}")
        
        # Auto-generate if needed
        auto_generate_if_needed(project_dir)
        
        return 0
    else:
        print("❌ Failed to create file")
        return 1


def determine_file_location(file_type: str, project_dir: Path, location: str = None) -> Tuple[str, Path]:
    """Determine file extension and target directory."""
    
    # Map file types to extensions
    type_to_ext = {
        "class": ("h", "cpp"),
        "struct": ("h", "cpp"),
        "enum": ("h", ""),
        "union": ("h", ""),
        "interface": ("h", ""),
        "header": ("h", ""),
        "h": ("h", ""),
        "source": ("cpp", ""),
        "cpp": ("cpp", ""),
        "c": ("c", ""),
        "m": ("m", ""),
        "mm": ("mm", ""),
        "inl": ("inl", ""),
        "text": ("txt", ""),
    }
    
    ext_info = type_to_ext.get(file_type, ("txt", ""))
    header_ext = ext_info[0]
    source_ext = ext_info[1] if len(ext_info) > 1 else ""
    
    # Determine target directory
    if location:
        target_dir = project_dir / location
    elif file_type in ["header", "h"]:
        # ✅ MODIFICATION: Créer dans le dossier du projet
        target_dir = project_dir / "include" / project_dir.name
    elif file_type in ["class", "struct", "enum", "union", "interface"]:
        # ✅ MODIFICATION: Créer dans le dossier du projet
        target_dir = project_dir / "src" / project_dir.name
    elif file_type in ["source", "cpp", "c", "m", "mm", "inl"]:
        # ✅ MODIFICATION: Créer dans le dossier du projet
        target_dir = project_dir / "src" / project_dir.name
    else:
        target_dir = project_dir
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    return header_ext, target_dir


def create_file_by_type(
    name: str,
    file_type: str,
    file_ext: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> Optional[Path]:
    """Create file based on type."""
    
    if file_type in ["class", "struct", "enum", "union", "interface"]:
        return create_cpp_composite_file(
            name=name,
            file_type=file_type,
            target_dir=target_dir,
            project_name=project_name,
            namespace=namespace
        )
    elif file_type in ["header", "h"]:
        return create_header_file_simple(
            name=name,
            target_dir=target_dir,
            project_name=project_name,
            namespace=namespace
        )
    elif file_type in ["source", "cpp", "c"]:
        return create_source_file_simple(
            name=name,
            file_ext=file_ext,
            target_dir=target_dir,
            project_name=project_name,
            namespace=namespace
        )
    elif file_type in ["m", "mm"]:
        return create_objectivec_file_simple(
            name=name,
            file_ext=file_ext,
            target_dir=target_dir,
            project_name=project_name
        )
    elif file_type == "inl":
        return create_inline_file_simple(
            name=name,
            target_dir=target_dir,
            project_name=project_name,
            namespace=namespace
        )
    elif file_type == "text":
        return create_text_file_simple(
            name=name,
            target_dir=target_dir
        )
    else:
        print(f"❌ Unknown file type: {file_type}")
        return None


def create_cpp_composite_file(
    name: str,
    file_type: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> Optional[Path]:
    """Create C++ class/struct/enum files."""
    
    # Create header file
    header_file = create_cpp_header_file(
        name=name,
        file_type=file_type,
        target_dir=target_dir,
        project_name=project_name,
        namespace=namespace
    )
    
    if not header_file:
        return None
    
    # Create source file for types that need it
    if file_type in ["class", "struct"]:
        source_file = create_cpp_source_file(
            name=name,
            file_type=file_type,
            target_dir=target_dir,
            project_name=project_name,
            namespace=namespace
        )
        
        if source_file:
            print(f"✅ Created: {source_file.relative_to(Path.cwd())}")
    
    return header_file


def create_cpp_header_file(
    name: str,
    file_type: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> Optional[Path]:
    """Create C++ header file."""
    
    guard = f"{project_name.upper()}_{name.upper()}_H"
    header_file = target_dir / f"{name}.h"
    
    # Get description based on file type
    descriptions = {
        "class": f"{name} class",
        "struct": f"{name} structure",
        "enum": f"{name} enumeration",
        "union": f"{name} union",
        "interface": f"{name} interface",
    }
    
    description = descriptions.get(file_type, f"{name} header")
    
    content = get_file_header(
        filename=f"{name}.h",
        description=description,
        file_type="h"
    )
    
    content += f'''#pragma once
#ifndef {guard}
#define {guard}

#include <cstdint>
#include <string>
'''
    
    # Add namespace if specified
    if namespace:
        content += f'''
namespace {namespace} {{
'''
    
    # Add class/struct/enum definition
    if file_type == "class":
        content += f'''
/**
 * @class {name}
 * @brief {name} class
 */
class {name} {{
public:
    /**
     * @brief Default constructor
     */
    {name}();
    
    /**
     * @brief Destructor
     */
    virtual ~{name}();
    
    /**
     * @brief Copy constructor
     */
    {name}(const {name}& other);
    
    /**
     * @brief Move constructor
     */
    {name}({name}&& other) noexcept;
    
    /**
     * @brief Copy assignment operator
     */
    {name}& operator=(const {name}& other);
    
    /**
     * @brief Move assignment operator
     */
    {name}& operator=({name}&& other) noexcept;
    
    /**
     * @brief Initialize the {name}
     * @return True if successful
     */
    bool initialize();
    
    /**
     * @brief Get the name
     * @return Name string
     */
    std::string getName() const;
    
    /**
     * @brief Set the name
     * @param name New name
     */
    void setName(const std::string& name);
    
private:
    std::string m_name;
}};
'''
    elif file_type == "struct":
        content += f'''
/**
 * @struct {name}
 * @brief {name} structure
 */
struct {name} {{
    // Public members
    int id;
    std::string name;
    float value;
    
    /**
     * @brief Default constructor
     */
    {name}();
    
    /**
     * @brief Parameterized constructor
     * @param id ID
     * @param name Name
     * @param value Value
     */
    {name}(int id, const std::string& name, float value);
    
    /**
     * @brief Check if valid
     * @return True if valid
     */
    bool isValid() const;
    
    /**
     * @brief Reset to default values
     */
    void reset();
}};
'''
    elif file_type == "enum":
        content += f'''
/**
 * @enum {name}
 * @brief {name} enumeration
 */
enum class {name} : uint32_t {{
    None = 0,
    First,
    Second,
    Third,
    Max
}};

/**
 * @brief Convert {name} to string
 * @param value Enum value
 * @return String representation
 */
std::string toString({name} value);

/**
 * @brief Convert string to {name}
 * @param str String representation
 * @return Enum value
 */
{name} fromString(const std::string& str);
'''
    elif file_type == "union":
        content += f'''
/**
 * @union {name}
 * @brief {name} union
 */
union {name} {{
    int int_value;
    float float_value;
    double double_value;
    char char_value;
    void* ptr_value;
    
    /**
     * @brief Default constructor
     */
    {name}();
    
    /**
     * @brief Destructor
     */
    ~{name}();
    
    /**
     * @brief Reset all values to zero
     */
    void clear();
}};
'''
    elif file_type == "interface":
        content += f'''
/**
 * @class {name}
 * @brief {name} interface
 */
class {name} {{
public:
    virtual ~{name}() = default;
    
    /**
     * @brief Initialize the interface
     * @return True if successful
     */
    virtual bool initialize() = 0;
    
    /**
     * @brief Shutdown the interface
     */
    virtual void shutdown() = 0;
    
    /**
     * @brief Check if initialized
     * @return True if initialized
     */
    virtual bool isInitialized() const = 0;
    
protected:
    {name}() = default;
    
private:
    # Disable copying
    {name}(const {name}&) = delete;
    {name}& operator=(const {name}&) = delete;
    
    # Disable moving
    {name}({name}&&) = delete;
    {name}& operator=({name}&&) = delete;
}};
'''
    
    # Close namespace if opened
    if namespace:
        content += f'''
}} // namespace {namespace}
'''
    
    content += f'''
#endif // {guard}
'''
    
    content += get_file_footer(f"{name}.h", "h")
    
    try:
        header_file.write_text(content, encoding='utf-8')
        print(f"✅ Created: {header_file.relative_to(Path.cwd())}")
        return header_file
    except Exception as e:
        print(f"❌ Failed to create header file: {e}")
        return None


def create_cpp_source_file(
    name: str,
    file_type: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> Optional[Path]:
    """Create C++ source file."""
    
    source_file = target_dir / f"{name}.cpp"
    
    content = get_file_header(
        filename=f"{name}.cpp",
        description=f"Implementation of {name} {file_type}",
        file_type="cpp"
    )
    
    content += f'''#include "{name}.h"
#include <algorithm>
#include <utility>
'''
    
    # Add namespace if specified
    if namespace:
        content += f'''
namespace {namespace} {{
'''
    
    # Add implementation based on file type
    if file_type == "class":
        content += f'''
// {name} implementation

{name}::{name}() : m_name("Unnamed") {{
    // Default constructor
}}

{name}::~{name}() {{
    // Destructor
}}

{name}::{name}(const {name}& other) : m_name(other.m_name) {{
    // Copy constructor
}}

{name}::{name}({name}&& other) noexcept : m_name(std::move(other.m_name)) {{
    // Move constructor
}}

{name}& {name}::operator=(const {name}& other) {{
    if (this != &other) {{
        m_name = other.m_name;
    }}
    return *this;
}}

{name}& {name}::operator=({name}&& other) noexcept {{
    if (this != &other) {{
        m_name = std::move(other.m_name);
    }}
    return *this;
}}

bool {name}::initialize() {{
    // Initialize implementation
    return true;
}}

std::string {name}::getName() const {{
    return m_name;
}}

void {name}::setName(const std::string& name) {{
    m_name = name;
}}
'''
    elif file_type == "struct":
        content += f'''
// {name} implementation

{name}::{name}() : id(0), name("Unnamed"), value(0.0f) {{
    // Default constructor
}}

{name}::{name}(int id, const std::string& name, float value) 
    : id(id), name(name), value(value) {{
    // Parameterized constructor
}}

bool {name}::isValid() const {{
    return id > 0 && !name.empty();
}}

void {name}::reset() {{
    id = 0;
    name.clear();
    value = 0.0f;
}}
'''
    
    # Close namespace if opened
    if namespace:
        content += f'''
}} // namespace {namespace}
'''
    
    content += get_file_footer(f"{name}.cpp", "cpp")
    
    try:
        source_file.write_text(content, encoding='utf-8')
        return source_file
    except Exception as e:
        print(f"❌ Failed to create source file: {e}")
        return None


def create_header_file_simple(
    name: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> Path:
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
    
    // Add your declarations here
    
}} // namespace {namespace}
'''
    else:
        content += '''// Add your declarations here
'''
    
    content += f'''
#endif // {guard}
'''
    
    content += get_file_footer(f"{name}.h", "h")
    
    header_file.write_text(content, encoding='utf-8')
    return header_file


def create_source_file_simple(
    name: str,
    file_ext: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> Path:
    """Create simple source file."""
    
    source_file = target_dir / f"{name}.{file_ext}"
    
    content = get_file_header(
        filename=f"{name}.{file_ext}",
        description=f"{name} implementation",
        file_type=file_ext
    )
    
    if file_ext == "cpp":
        content += '''#include <iostream>
#include <cstdlib>

'''
        if namespace:
            content += f'''namespace {namespace} {{
    
    // Add your implementation here
    
}} // namespace {namespace}
'''
        else:
            content += '''// Add your implementation here
'''
        
        content += '''

int main() {
    std::cout << "Hello from ''' + name + '''!" << std::endl;
    return EXIT_SUCCESS;
}
'''
    elif file_ext == "c":
        content += '''#include <stdio.h>
#include <stdlib.h>

// Add your C implementation here

int main() {
    printf("Hello from ''' + name + '''!\\n");
    return EXIT_SUCCESS;
}
'''
    
    content += get_file_footer(f"{name}.{file_ext}", file_ext)
    
    source_file.write_text(content, encoding='utf-8')
    return source_file


def create_objectivec_file_simple(
    name: str,
    file_ext: str,
    target_dir: Path,
    project_name: str
) -> Path:
    """Create Objective-C/C++ file."""
    
    source_file = target_dir / f"{name}.{file_ext}"
    
    content = get_file_header(
        filename=f"{name}.{file_ext}",
        description=f"{name} Objective-C implementation",
        file_type=file_ext
    )
    
    if file_ext == "m":
        content += '''#import <Foundation/Foundation.h>

@interface ''' + name + ''' : NSObject

@property (nonatomic, strong) NSString *name;

- (instancetype)initWithName:(NSString *)name;
- (void)printHello;

@end

@implementation ''' + name + '''

- (instancetype)initWithName:(NSString *)name {
    self = [super init];
    if (self) {
        _name = [name copy];
    }
    return self;
}

- (void)printHello {
    NSLog(@"Hello from %@", self.name);
}

@end
'''
    elif file_ext == "mm":
        content += '''#include <iostream>
#import <Foundation/Foundation.h>

class ''' + name + ''' {
public:
    ''' + name + '''() {
        std::cout << "''' + name + ''' created" << std::endl;
    }
    
    void sayHello() {
        std::cout << "Hello from ''' + name + '''" << std::endl;
    }
};
'''
    
    content += get_file_footer(f"{name}.{file_ext}", file_ext)
    
    source_file.write_text(content, encoding='utf-8')
    return source_file


def create_inline_file_simple(
    name: str,
    target_dir: Path,
    project_name: str,
    namespace: str = None
) -> Path:
    """Create inline header file."""
    
    inline_file = target_dir / f"{name}.inl"
    guard = f"{project_name.upper()}_{name.upper()}_INL"
    
    content = get_file_header(
        filename=f"{name}.inl",
        description=f"{name} inline implementations",
        file_type="inl"
    )
    
    content += f'''#ifndef {guard}
#define {guard}

'''
    
    if namespace:
        content += f'''namespace {namespace} {{
    
    // Inline implementations
    
}} // namespace {namespace}
'''
    else:
        content += '''// Inline implementations
'''
    
    content += f'''
#endif // {guard}
'''
    
    content += get_file_footer(f"{name}.inl", "inl")
    
    inline_file.write_text(content, encoding='utf-8')
    return inline_file


def create_text_file_simple(name: str, target_dir: Path) -> Path:
    """Create text file."""
    
    text_file = target_dir / f"{name}.txt"
    
    content = get_file_header(
        filename=f"{name}.txt",
        description=f"{name} text file",
        file_type="txt"
    )
    
    content += f'''{name}
========

Created with Jenga Build System v{VERSION}

Description:
Add your text content here.

Configuration:
1. File: {name}.txt
2. Location: {target_dir}
3. Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Notes:
1. 
2. 
3. 
'''
    
    content += get_file_footer(f"{name}.txt", "txt")
    
    text_file.write_text(content, encoding='utf-8')
    return text_file


def auto_generate_if_needed(project_dir: Path) -> None:
    """Auto-generate project files if needed."""
    
    jenga_files = list(project_dir.glob("*.jenga"))
    if jenga_files:
        print(f"\n🔧 Regenerating project files...")
        try:
            from Jenga.Commands.gen import generate
            generate(jenga_file=str(jenga_files[0]))
        except ImportError:
            print("⚠️  Could not auto-generate project files")
        except Exception as e:
            print(f"⚠️  Auto-generation failed: {e}")


def auto_generate_project_files(jenga_file: Path) -> None:
    """Auto-generate project files for a workspace."""
    
    print(f"\n🔧 Generating project files...")
    try:
        from Jenga.Commands.gen import generate
        generate(jenga_file=str(jenga_file))
    except ImportError:
        print("⚠️  Could not auto-generate project files")
    except Exception as e:
        print(f"⚠️  Auto-generation failed: {e}")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def execute(args):
    """Main entry point for create command."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create workspaces, projects, and files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
Examples:
  jenga create workspace                  # Interactive workspace creation
  jenga create workspace MyGame           # Quick workspace with default settings
  jenga create project                    # Interactive project creation
  jenga create project Engine --type staticlib
  jenga create project Tools --location utils/tools
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
        help='Where to create main project (relative to workspace)'
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
        help='Where to create project (relative to workspace)'
    )
    proj_parser.add_argument(
        '--namespace',
        help='Main namespace for the project'
    )
    proj_parser.add_argument(
        '--sub-namespaces',
        help='Sub-namespaces (comma separated)'
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
        choices=[
            'class', 'struct', 'enum', 'union', 'interface',
            'header', 'source', 'cpp', 'c', 'm', 'mm', 'inl', 'text'
        ],
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
                main_project_namespace=parsed.namespace,
                project_name=parsed.project_name,
                project_location=parsed.project_location
            )
        else:
            # Interactive creation
            return create_workspace_interactive()
    
    elif parsed.subcommand == 'project':
        if parsed.name:
            # Quick creation with arguments
            sub_namespaces = []
            if parsed.sub_namespaces:
                sub_namespaces = [ns.strip() for ns in parsed.sub_namespaces.split(',')]
            
            return create_project(
                name=parsed.name,
                project_type=parsed.type,
                location=parsed.location,
                main_namespace=parsed.namespace,
                sub_namespaces=sub_namespaces
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