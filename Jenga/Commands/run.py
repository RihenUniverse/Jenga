#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Run Command
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.variables import VariableExpander
from core.api import ProjectKind
from utils.display import Display


def execute(options: dict) -> bool:
    """Execute run command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    config = options.get("config", "Debug")
    platform = options.get("platform", "Windows")
    project_name = options.get("project", workspace.startproject)
    
    # Find project to run
    if not project_name:
        # Find first executable project
        for name, proj in workspace.projects.items():
            if proj.kind in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP]:
                project_name = name
                break
    
    if not project_name:
        Display.error("No executable project found to run")
        return False
    
    if project_name not in workspace.projects:
        Display.error(f"Project not found: {project_name}")
        return False
    
    project = workspace.projects[project_name]
    
    # Check if it's executable
    if project.kind not in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE]:
        Display.error(f"Project '{project_name}' is not executable")
        return False
    
    # Get executable path
    expander = VariableExpander(workspace, project, config, platform)
    target_dir = Path(expander.expand(project.targetdir))
    target_name = project.targetname or project.name
    
    # Determine executable extension
    if platform == "Windows":
        executable = target_dir / f"{target_name}.exe"
    else:
        executable = target_dir / target_name
    
    if not executable.exists():
        Display.error(f"Executable not found: {executable}")
        Display.info("Try building first with: nken build")
        return False
    
    Display.info(f"Running: {executable}")
    print("=" * 60)
    
    # Run the executable
    try:
        result = subprocess.run(
            [str(executable)],
            cwd=workspace.location
        )
        
        print("=" * 60)
        
        if result.returncode == 0:
            Display.success(f"Program exited with code 0")
        else:
            Display.warning(f"Program exited with code {result.returncode}")
        
        return result.returncode == 0
        
    except FileNotFoundError:
        Display.error(f"Could not execute: {executable}")
        return False
    except KeyboardInterrupt:
        Display.warning("\nProgram interrupted")
        return False
    except Exception as e:
        Display.error(f"Error running program: {e}")
        return False


if __name__ == "__main__":
    execute({})
