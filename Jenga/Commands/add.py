#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Add Command
Add external libraries and dependencies to projects
"""

import sys
import os
import subprocess
import shutil
import json
from pathlib import Path
from urllib.request import urlretrieve

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from utils.display import Display, Colors


# Library registry
LIBRARY_REGISTRY = {
    "sdl2": {
        "name": "SDL2",
        "type": "system",
        "include": "SDL2",
        "links": ["SDL2"],
        "homepage": "https://www.libsdl.org/",
        "git": "https://github.com/libsdl-org/SDL.git",
    },
    "sfml": {
        "name": "SFML",
        "type": "system",
        "include": "SFML",
        "links": ["sfml-graphics", "sfml-window", "sfml-system"],
        "homepage": "https://www.sfml-dev.org/",
        "git": "https://github.com/SFML/SFML.git",
    },
    "glfw": {
        "name": "GLFW",
        "type": "system",
        "include": "GLFW",
        "links": ["glfw"],
        "homepage": "https://www.glfw.org/",
        "git": "https://github.com/glfw/glfw.git",
    },
    "glm": {
        "name": "GLM",
        "type": "header-only",
        "include": "glm",
        "homepage": "https://glm.g-truc.net/",
        "git": "https://github.com/g-truc/glm.git",
    },
    "imgui": {
        "name": "Dear ImGui",
        "type": "source",
        "include": "imgui",
        "source": ["imgui/*.cpp"],
        "homepage": "https://github.com/ocornut/imgui",
        "git": "https://github.com/ocornut/imgui.git",
    },
    "json": {
        "name": "nlohmann/json",
        "type": "header-only",
        "include": "nlohmann",
        "homepage": "https://json.nlohmann.me/",
        "git": "https://github.com/nlohmann/json.git",
    },
    "spdlog": {
        "name": "spdlog",
        "type": "header-only",
        "include": "spdlog",
        "homepage": "https://github.com/gabime/spdlog",
        "git": "https://github.com/gabime/spdlog.git",
    },
    "boost": {
        "name": "Boost",
        "type": "system",
        "include": "boost",
        "homepage": "https://www.boost.org/",
    },
    "opengl": {
        "name": "OpenGL",
        "type": "system",
        "include": "",
        "links": ["GL", "GLU"],
        "windows_links": ["opengl32", "glu32"],
    },
    "vulkan": {
        "name": "Vulkan",
        "type": "system",
        "include": "vulkan",
        "links": ["vulkan"],
    },
}


def execute(args: list) -> int:
    """Main entry point for add command"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Add external libraries")
    subparsers = parser.add_subparsers(dest='subcommand', help='What to add')
    
    # Add library
    lib_parser = subparsers.add_parser('library', help='Add a library')
    lib_parser.add_argument('name', help='Library name (sdl2, sfml, glm, etc.)')
    lib_parser.add_argument('--project', help='Target project (default: all)')
    lib_parser.add_argument('--method', choices=['system', 'git', 'download', 'auto'],
                           default='auto', help='Installation method')
    lib_parser.add_argument('--git-url', help='Custom git repository URL')
    lib_parser.add_argument('--version', help='Specific version/tag')
    
    parsed = parser.parse_args(args)
    
    if parsed.subcommand == 'library':
        return add_library(parsed.name, parsed.project, parsed.method, 
                          parsed.git_url, parsed.version)
    else:
        parser.print_help()
        return 1


def add_library(name: str, project: str, method: str, git_url: str, version: str) -> int:
    """Add external library to project"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        Display.error("No workspace found")
        return 1
    
    Display.section(f"Adding Library: {name}")
    
    # Check if library is in registry
    lib_name_lower = name.lower()
    if lib_name_lower in LIBRARY_REGISTRY:
        lib_info = LIBRARY_REGISTRY[lib_name_lower]
        Display.info(f"Found: {lib_info['name']}")
    else:
        Display.warning(f"Library '{name}' not in registry")
        lib_info = {
            "name": name,
            "type": "unknown",
            "git": git_url,
        }
    
    # Determine installation method
    if method == 'auto':
        if lib_info.get('type') == 'system':
            method = 'system'
        elif lib_info.get('git'):
            method = 'git'
        else:
            method = 'download'
    
    Display.info(f"Method: {method}")
    
    # Install library
    if method == 'system':
        return _add_system_library(workspace, lib_info, project)
    elif method == 'git':
        git_repo = git_url or lib_info.get('git')
        if not git_repo:
            Display.error("No git repository URL specified")
            return 1
        return _add_git_library(workspace, lib_info, git_repo, version, project)
    elif method == 'download':
        Display.error("Download method not implemented yet")
        return 1
    
    return 0


def _add_system_library(workspace, lib_info: dict, project_name: str) -> int:
    """Add system-installed library"""
    
    Display.step("Adding system library...")
    
    # Check if library is installed
    lib_name = lib_info['name']
    
    # Try pkg-config first
    has_pkgconfig = False
    try:
        result = subprocess.run(['pkg-config', '--exists', lib_name.lower()],
                              capture_output=True)
        has_pkgconfig = (result.returncode == 0)
    except FileNotFoundError:
        pass
    
    if has_pkgconfig:
        Display.success(f"✓ Found {lib_name} via pkg-config")
        
        # Get flags
        result = subprocess.run(['pkg-config', '--cflags', lib_name.lower()],
                              capture_output=True, text=True)
        cflags = result.stdout.strip()
        
        result = subprocess.run(['pkg-config', '--libs', lib_name.lower()],
                              capture_output=True, text=True)
        libs = result.stdout.strip()
        
        Display.info(f"CFLAGS: {cflags}")
        Display.info(f"LIBS: {libs}")
    else:
        Display.warning(f"{lib_name} not found via pkg-config")
        Display.info("Assuming standard system paths...")
    
    # Update .jenga file
    jenga_files = list(Path(".").glob("*.jenga"))
    if not jenga_files:
        Display.error("No .jenga file found")
        return 1
    
    jenga_file = jenga_files[0]
    
    # Read current content
    content = jenga_file.read_text()
    
    # Determine what to add
    includes = []
    links = []
    
    if 'include' in lib_info and lib_info['include']:
        includes.append(lib_info['include'])
    
    if 'links' in lib_info:
        links = lib_info['links']
    
    # Add to specific project or all projects
    if project_name:
        if f'with project("{project_name}")' not in content:
            Display.error(f"Project '{project_name}' not found in {jenga_file}")
            return 1
        
        # Add to specific project
        Display.info(f"Adding to project: {project_name}")
        # TODO: Parse and modify specific project
        
    else:
        # Add to all projects
        Display.info("Adding to all projects (manual edit required)")
    
    # Create a snippet to add manually
    snippet = f"""
    # {lib_info['name']} library
"""
    
    if includes:
        snippet += f"    # includedirs([\"{'/'.join(includes)}\"])\n"
    
    if links:
        links_str = '", "'.join(links)
        snippet += f'    links(["{links_str}"])\n'
    
    Display.success("\n✓ Library configured")
    Display.info("\nAdd this to your project in .jenga file:")
    print(Colors.CYAN + snippet + Colors.RESET)
    
    return 0


def _add_git_library(workspace, lib_info: dict, git_url: str, version: str, project_name: str) -> int:
    """Add library from git repository"""
    
    Display.step(f"Cloning from git: {git_url}")
    
    # Create external directory
    external_dir = Path(workspace.location) / "external"
    external_dir.mkdir(exist_ok=True)
    
    # Library directory name
    lib_name = lib_info['name'].replace('/', '_').replace(' ', '_')
    lib_dir = external_dir / lib_name
    
    if lib_dir.exists():
        Display.warning(f"Directory {lib_dir} already exists")
        response = input("Overwrite? [y/N]: ")
        if response.lower() != 'y':
            Display.info("Aborted")
            return 1
        shutil.rmtree(lib_dir)
    
    # Clone repository
    Display.info("Cloning repository...")
    try:
        cmd = ['git', 'clone', git_url, str(lib_dir)]
        if version:
            cmd.extend(['--branch', version])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            Display.error(f"Git clone failed: {result.stderr}")
            return 1
        
        Display.success("✓ Repository cloned")
        
    except Exception as e:
        Display.error(f"Failed to clone: {e}")
        return 1
    
    # Determine library type and setup
    lib_type = lib_info.get('type', 'unknown')
    
    if lib_type == 'header-only':
        Display.info("Header-only library detected")
        
        # Find include directory
        possible_includes = [
            lib_dir / "include",
            lib_dir / "src",
            lib_dir,
        ]
        
        include_dir = None
        for inc in possible_includes:
            if inc.exists() and list(inc.glob("**/*.h*")):
                include_dir = inc
                break
        
        if include_dir:
            Display.success(f"✓ Include directory: {include_dir.relative_to(workspace.location)}")
        else:
            Display.warning("Could not detect include directory")
            include_dir = lib_dir
    
    elif lib_type == 'source':
        Display.info("Source library detected")
        
        # Check for .jenga file
        jenga_files = list(lib_dir.glob("*.jenga"))
        if jenga_files:
            Display.success(f"✓ Found Jenga file: {jenga_files[0].name}")
            Display.info("You can include this project with:")
            print(f'    include("external/{lib_name}/{jenga_files[0].name}")')
        else:
            Display.info("No .jenga file found, you'll need to configure manually")
    
    else:
        Display.info("Checking build system...")
        
        # Check for CMake
        if (lib_dir / "CMakeLists.txt").exists():
            Display.info("CMake project detected")
            Display.info("Build with: cd external/{} && cmake . && make".format(lib_name))
        
        # Check for configure
        elif (lib_dir / "configure").exists():
            Display.info("Autotools project detected")
            Display.info("Build with: cd external/{} && ./configure && make".format(lib_name))
    
    # Create usage snippet
    Display.success("\n✓ Library downloaded to: external/{}".format(lib_name))
    
    snippet = f"""
    # {lib_info['name']} (from external/{lib_name})
    includedirs(["external/{lib_name}/include"])
"""
    
    if lib_type == 'source' and 'source' in lib_info:
        snippet += f'    files(["external/{lib_name}/{lib_info["source"][0]}"])\n'
    
    Display.info("\nAdd this to your project:")
    print(Colors.CYAN + snippet + Colors.RESET)
    
    return 0


if __name__ == "__main__":
    sys.exit(execute(sys.argv[1:]))