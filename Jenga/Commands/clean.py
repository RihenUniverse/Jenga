#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Clean Command
"""

import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.variables import VariableExpander
from utils.reporter import Reporter
from utils.display import Display


def execute(options: dict) -> bool:
    """Execute clean command"""
    
    Reporter.start()
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    config = options.get("config", "Debug")
    platform = options.get("platform", "Windows")
    project_name = options.get("project", None)
    
    Reporter.section("Cleaning build artifacts")
    
    # Clean specific project or all projects
    if project_name:
        if project_name not in workspace.projects:
            Display.error(f"Project not found: {project_name}")
            return False
        
        projects_to_clean = [workspace.projects[project_name]]
    else:
        projects_to_clean = list(workspace.projects.values())
    
    cleaned_count = 0
    
    for project in projects_to_clean:
        if clean_project(project, workspace, config, platform):
            cleaned_count += 1
    
    # Clean cache
    cache_dir = Path(workspace.location) / ".nken_cache"
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            Display.info("Cleaned build cache")
        except Exception as e:
            Display.warning(f"Failed to clean cache: {e}")
    
    Reporter.end()
    Display.success(f"Cleaned {cleaned_count} project(s)")
    
    return True


def clean_project(project, workspace, config: str, platform: str) -> bool:
    """Clean a single project"""
    
    expander = VariableExpander(workspace, project, config, platform)
    
    # Clean object directory
    if project.objdir:
        obj_dir = Path(expander.expand(project.objdir))
        if obj_dir.exists():
            try:
                shutil.rmtree(obj_dir)
                Display.info(f"Cleaned: {project.name} (objects)")
            except Exception as e:
                Display.warning(f"Failed to clean {project.name}: {e}")
                return False
    
    # Clean target directory
    if project.targetdir:
        target_dir = Path(expander.expand(project.targetdir))
        if target_dir.exists():
            try:
                # Remove only the output file, not the entire directory
                # (directory may contain other projects)
                target_name = project.targetname or project.name
                
                # Try different extensions
                for ext in [".exe", ".dll", ".so", ".dylib", ".a", ".lib", ""]:
                    output_file = target_dir / f"{target_name}{ext}"
                    if output_file.exists():
                        output_file.unlink()
                
                Display.info(f"Cleaned: {project.name} (target)")
            except Exception as e:
                Display.warning(f"Failed to clean target for {project.name}: {e}")
    
    return True


if __name__ == "__main__":
    execute({})
