#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Gen Command
Generate IDE configuration files (VSCode, Visual Studio, etc.)
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.variables import VariableExpander
from utils.display import Display


def execute(options: dict) -> bool:
    """Execute gen command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    # Get options
    ide = options.get("ide", "vscode")  # Default to VSCode
    config = options.get("config", "Debug")
    platform_name = options.get("platform", "Linux")
    
    Display.info(f"Generating {ide.upper()} configuration...")
    
    if ide.lower() == "vscode":
        return generate_vscode(workspace, config, platform_name)
    else:
        Display.error(f"IDE '{ide}' not yet supported")
        Display.info("Supported IDEs: vscode")
        return False


def generate_vscode(workspace, config: str, platform: str) -> bool:
    """Generate VSCode configuration files"""
    
    # Create .vscode directory
    vscode_dir = Path(workspace.location) / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    
    # Generate c_cpp_properties.json
    if not generate_cpp_properties(workspace, config, platform, vscode_dir):
        return False
    
    # Generate tasks.json
    if not generate_tasks(workspace, config, platform, vscode_dir):
        return False
    
    # Generate launch.json
    if not generate_launch(workspace, config, platform, vscode_dir):
        return False
    
    Display.success(f"VSCode configuration generated in {vscode_dir}")
    Display.info("Files created:")
    Display.info("  - c_cpp_properties.json (IntelliSense)")
    Display.info("  - tasks.json (Build tasks)")
    Display.info("  - launch.json (Debug configurations)")
    
    return True


def generate_cpp_properties(workspace, config: str, platform: str, vscode_dir: Path) -> bool:
    """Generate c_cpp_properties.json for IntelliSense"""
    
    configurations = []
    
    for cfg_name in workspace.configurations:
        expander = VariableExpander(workspace, None, cfg_name, platform)
        
        # Collect all include paths from all projects
        include_paths = set()
        defines = set()
        
        for proj_name, project in workspace.projects.items():
            proj_expander = VariableExpander(workspace, project, cfg_name, platform)
            
            # Add project includes
            for inc_dir in project.includedirs:
                expanded = proj_expander.expand(inc_dir)
                include_paths.add(expanded)
            
            # Add project defines
            for define in project.defines:
                expanded = proj_expander.expand(define)
                defines.add(expanded)
            
            # Add filtered defines
            filter_key = f"configurations:{cfg_name}"
            if filter_key in project._filtered_defines:
                defines.update(project._filtered_defines[filter_key])
            
            filter_key = f"system:{platform}"
            if filter_key in project._filtered_defines:
                defines.update(project._filtered_defines[filter_key])
        
        # Determine compiler path
        if workspace.toolchains and "default" in workspace.toolchains:
            default_tc = workspace.toolchains["default"]
            compiler_path = default_tc.cppcompiler_path or default_tc.cppcompiler or default_tc.compiler
        else:
            compiler_path = "g++"
        
        # Determine C++ standard
        cpp_standard = "c++17"  # Default
        for project in workspace.projects.values():
            if project.cppdialect:
                std = project.cppdialect.lower().replace("c++", "c++")
                cpp_standard = std
                break
        
        # Build configuration
        cfg = {
            "name": f"{platform}-{cfg_name}",
            "includePath": sorted(list(include_paths)),
            "defines": sorted(list(defines)),
            "compilerPath": compiler_path,
            "cStandard": "c17",
            "cppStandard": cpp_standard,
            "intelliSenseMode": "gcc-x64" if platform == "Linux" else "msvc-x64"
        }
        
        configurations.append(cfg)
    
    # Write file
    cpp_props = {
        "version": 4,
        "configurations": configurations
    }
    
    cpp_props_file = vscode_dir / "c_cpp_properties.json"
    with open(cpp_props_file, 'w', encoding='utf-8') as f:
        json.dump(cpp_props, f, indent=4)
    
    Display.detail(f"  Created: {cpp_props_file.name}")
    return True


def generate_tasks(workspace, config: str, platform: str, vscode_dir: Path) -> bool:
    """Generate tasks.json for build tasks"""
    
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Nken: Build",
                "type": "shell",
                "command": "python3",
                "args": [
                    "Tools/nken.py",
                    "build",
                    "--config", config
                ],
                "group": {
                    "kind": "build",
                    "isDefault": True
                },
                "problemMatcher": ["$gcc"],
                "presentation": {
                    "reveal": "always",
                    "panel": "shared"
                }
            },
            {
                "label": "Nken: Clean",
                "type": "shell",
                "command": "python3",
                "args": [
                    "Tools/nken.py",
                    "clean"
                ],
                "group": "build",
                "presentation": {
                    "reveal": "always",
                    "panel": "shared"
                }
            },
            {
                "label": "Nken: Rebuild",
                "type": "shell",
                "command": "python3",
                "args": [
                    "Tools/nken.py",
                    "rebuild",
                    "--config", config
                ],
                "group": "build",
                "presentation": {
                    "reveal": "always",
                    "panel": "shared"
                }
            },
            {
                "label": "Nken: Run",
                "type": "shell",
                "command": "python3",
                "args": [
                    "Tools/nken.py",
                    "run",
                    "--config", config
                ],
                "group": "test",
                "presentation": {
                    "reveal": "always",
                    "panel": "shared"
                }
            }
        ]
    }
    
    tasks_file = vscode_dir / "tasks.json"
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=4)
    
    Display.detail(f"  Created: {tasks_file.name}")
    return True


def generate_launch(workspace, config: str, platform: str, vscode_dir: Path) -> bool:
    """Generate launch.json for debugging"""
    
    # Find executable projects
    configurations = []
    
    from core.api import ProjectKind
    
    for proj_name, project in workspace.projects.items():
        if project.kind not in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP]:
            continue
        
        expander = VariableExpander(workspace, project, config, platform)
        
        target_dir = expander.expand(project.targetdir)
        target_name = project.targetname or project.name
        
        # Determine executable path based on platform
        if platform == "Windows":
            program = f"{target_dir}/{target_name}.exe"
        else:
            program = f"{target_dir}/{target_name}"
        
        cfg = {
            "name": f"(gdb) Launch {proj_name}",
            "type": "cppdbg",
            "request": "launch",
            "program": program,
            "args": [],
            "stopAtEntry": False,
            "cwd": workspace.location,
            "environment": [],
            "externalConsole": False,
            "MIMode": "gdb",
            "preLaunchTask": "Nken: Build",
            "setupCommands": [
                {
                    "description": "Enable pretty-printing for gdb",
                    "text": "-enable-pretty-printing",
                    "ignoreFailures": True
                }
            ]
        }
        
        configurations.append(cfg)
    
    launch = {
        "version": "0.2.0",
        "configurations": configurations
    }
    
    launch_file = vscode_dir / "launch.json"
    with open(launch_file, 'w', encoding='utf-8') as f:
        json.dump(launch, f, indent=4)
    
    Display.detail(f"  Created: {launch_file.name}")
    return True


if __name__ == "__main__":
    # For testing
    execute({})
