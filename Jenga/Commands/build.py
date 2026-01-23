#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Build Command
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.buildsystem import Compiler
from utils.reporter import Reporter
from utils.display import Display


def execute(options: dict) -> bool:
    """Execute build command"""
    
    Reporter.start()
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    # Get options
    config = options.get("config", "Debug")
    platform = options.get("platform", "Windows")
    project_name = options.get("project", None)
    toolchain = options.get("toolchain", "default")
    jobs = int(options.get("jobs", 0)) or None
    use_cache = not options.get("no_cache", False)
    
    # Validate configuration
    if config not in workspace.configurations:
        Display.error(f"Invalid configuration: {config}")
        Display.info(f"Available configurations: {', '.join(workspace.configurations)}")
        return False
    
    # Validate platform
    if platform not in workspace.platforms:
        Display.error(f"Invalid platform: {platform}")
        Display.info(f"Available platforms: {', '.join(workspace.platforms)}")
        return False
    
    # Create compiler
    compiler = Compiler(workspace, config, platform, jobs, use_cache)
    
    # Build specific project or all projects
    if project_name:
        if project_name not in workspace.projects:
            Display.error(f"Project not found: {project_name}")
            Display.info(f"Available projects: {', '.join(workspace.projects.keys())}")
            return False
        
        project = workspace.projects[project_name]
        # Use project's toolchain if specified, otherwise use command line toolchain
        proj_toolchain = project.toolchain or toolchain
        success = compiler.compile_project(project, proj_toolchain)
    
    else:
        # Build all projects (respecting dependencies)
        success = build_all_projects(compiler, workspace, toolchain)
    
    # Print statistics
    compiler.print_stats()
    
    Reporter.end()
    
    if success:
        Display.success("Build completed successfully")
    else:
        Display.error("Build failed")
    
    return success


def build_all_projects(compiler: Compiler, workspace, toolchain: str) -> bool:
    """Build all projects in dependency order"""
    
    # Get build order
    build_order = get_build_order(workspace)
    
    if not build_order:
        Display.error("Failed to determine build order")
        return False
    
    Display.info(f"Building {len(build_order)} project(s) in dependency order")
    Display.info(f"Build order: {' -> '.join(build_order)}")
    
    # Build each project
    for project_name in build_order:
        project = workspace.projects[project_name]
        
        # Use project's toolchain if specified, otherwise use command line toolchain
        proj_toolchain = project.toolchain or toolchain
        
        if not compiler.compile_project(project, proj_toolchain):
            return False
    
    return True


def get_build_order(workspace) -> list:
    """
    Get projects in dependency order using topological sort
    Returns None if circular dependency detected
    
    Build order: dependencies FIRST, dependents LAST
    """
    
    # Build dependency graph: graph[project] = list of projects it depends on
    graph = {}
    in_degree = {}  # How many dependencies each project has
    
    for name, project in workspace.projects.items():
        graph[name] = project.dependson.copy()
        in_degree[name] = len(project.dependson)
    
    # Topological sort using Kahn's algorithm
    # Start with projects that have NO dependencies
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        # Sort to ensure deterministic order
        queue.sort()
        current = queue.pop(0)
        result.append(current)
        
        # Find all projects that depend on current
        for name in graph:
            if current in graph[name]:
                graph[name].remove(current)
                in_degree[name] -= 1
                if in_degree[name] == 0:
                    queue.append(name)
    
    # Check for circular dependencies
    if len(result) != len(workspace.projects):
        Display.error("Circular dependency detected:")
        for name, deps in graph.items():
            if deps:
                Display.error(f"  {name} still depends on: {', '.join(deps)}")
        return None
    
    # Result is already in correct order: dependencies first
    return result


if __name__ == "__main__":
    # For testing
    execute({})
