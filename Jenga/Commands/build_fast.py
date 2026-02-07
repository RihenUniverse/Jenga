#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Fast Build Command
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.buildsystem_fast import UltraFastCompiler, BuildMode
from utils.reporter import Reporter
from utils.display import Display


def execute(options: dict) -> bool:
    """Execute build command with ultra-fast mode"""
    
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
    
    # Build mode
    mode_str = options.get("mode", "ultra").upper()
    try:
        mode = BuildMode[mode_str]
    except KeyError:
        mode = BuildMode.ULTRA
        Display.warning(f"Unknown mode '{mode_str}', using 'ULTRA'")
    
    # Cache options
    use_cache = not options.get("no_cache", False)
    force_rebuild = options.get("force", False)
    
    if force_rebuild:
        Display.warning("Force rebuild enabled - cache will be ignored")
        use_cache = False
    
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
    compiler = UltraFastCompiler(workspace, config, platform, jobs, use_cache, mode)
    
    # Build specific project or all projects
    if project_name:
        if project_name not in workspace.projects:
            Display.error(f"Project not found: {project_name}")
            Display.info(f"Available projects: {', '.join(workspace.projects.keys())}")
            return False
        
        project = workspace.projects[project_name]
        proj_toolchain = project.toolchain or toolchain
        success = compiler.compile_project(project, proj_toolchain)
    
    else:
        # Build all projects (respecting dependencies)
        success = build_all_projects_fast(compiler, workspace, toolchain, force_rebuild)
    
    # Print statistics
    compiler.print_stats()
    
    Reporter.end()
    
    if success:
        Display.success("✅ Build completed successfully")
    else:
        Display.error("❌ Build failed")
    
    return success


def build_all_projects_fast(compiler: UltraFastCompiler, workspace, 
                          toolchain: str, force_rebuild: bool) -> bool:
    """Build all projects in dependency order (fast version)"""
    
    # Get build order
    build_order = get_build_order_fast(workspace)
    
    if not build_order:
        Display.error("Failed to determine build order")
        return False
    
    Display.info(f"📦 Building {len(build_order)} project(s) in dependency order")
    Display.info(f"🔗 Build order: {' → '.join(build_order)}")
    
    # Nettoyer le cache si force rebuild
    if force_rebuild and compiler.cache:
        compiler.cache.cache_data.clear()
        compiler.cache.deps_cache.clear()
        Display.info("🧹 Cache cleared (force rebuild)")
    
    # Build each project
    for project_name in build_order:
        project = workspace.projects[project_name]
        proj_toolchain = project.toolchain or toolchain
        
        if not compiler.compile_project(project, proj_toolchain):
            return False
    
    return True


def get_build_order_fast(workspace) -> list:
    """
    Get projects in dependency order (fast topological sort)
    """
    
    # Graph des dépendances
    graph = {}
    in_degree = {}
    
    for name, project in workspace.projects.items():
        # Filtrer les projets cachés comme __Unitest__
        if name.startswith("__"):
            continue
        
        deps = [d for d in project.dependson if d in workspace.projects]
        graph[name] = deps
        in_degree[name] = len(deps)
    
    # Tri topologique (Kahn)
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        # Trier pour un ordre déterministe
        queue.sort()
        current = queue.pop(0)
        result.append(current)
        
        # Mettre à jour les dépendances
        for name in graph:
            if current in graph[name]:
                in_degree[name] -= 1
                if in_degree[name] == 0:
                    queue.append(name)
    
    # Vérifier les dépendances circulaires
    if len(result) != len(graph):
        remaining = [name for name, degree in in_degree.items() if degree > 0]
        if remaining:
            Display.error("Circular dependency detected:")
            for name in remaining:
                Display.error(f"  {name} depends on: {', '.join(graph[name])}")
            return []
    
    return result


if __name__ == "__main__":
    # For testing
    execute({"mode": "ultra", "jobs": 4})