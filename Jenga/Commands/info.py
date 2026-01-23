#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Info Command
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from utils.display import Display, Colors


def execute(options: dict) -> bool:
    """Execute info command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    # Display workspace information
    print()
    Display.section("Workspace Information")
    
    print(f"{Colors.BOLD}Name:{Colors.RESET} {workspace.name}")
    print(f"{Colors.BOLD}Location:{Colors.RESET} {workspace.location}")
    print(f"{Colors.BOLD}Configurations:{Colors.RESET} {', '.join(workspace.configurations)}")
    print(f"{Colors.BOLD}Platforms:{Colors.RESET} {', '.join(workspace.platforms)}")
    
    if workspace.startproject:
        print(f"{Colors.BOLD}Start Project:{Colors.RESET} {workspace.startproject}")
    
    # Display toolchains
    if workspace.toolchains:
        print(f"\n{Colors.BOLD}Toolchains:{Colors.RESET}")
        for name, tc in workspace.toolchains.items():
            print(f"  • {name}: {tc.compiler}")
    
    # Display projects (filter hidden ones starting with __)
    Display.section("Projects")
    
    visible_projects = {name: proj for name, proj in workspace.projects.items() 
                       if not name.startswith("__")}
    
    for name, project in visible_projects.items():
        print(f"\n{Colors.BOLD}{Colors.CYAN}Project: {name}{Colors.RESET}")
        print(f"  Kind: {project.kind.value}")
        print(f"  Language: {project.language.value}")
        
        if project.cppdialect:
            print(f"  C++ Standard: {project.cppdialect}")
        
        if project.files:
            print(f"  Files: {len(project.files)} pattern(s)")
        
        if project.includedirs:
            print(f"  Include Dirs: {len(project.includedirs)}")
        
        if project.dependson:
            print(f"  Dependencies: {', '.join(project.dependson)}")
        
        if project.links:
            print(f"  Links: {', '.join(project.links)}")
        
        if project.targetdir:
            print(f"  Target Dir: {project.targetdir}")
    
    print()
    return True


if __name__ == "__main__":
    execute({})
