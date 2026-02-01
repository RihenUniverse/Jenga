#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Enhanced Run Command
Supports running executables with debuggers (GDB, GGDB, LLDB)
"""

import sys
import subprocess
import shlex
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.variables import VariableExpander
from core.api import ProjectKind
from utils.display import Display


# ============================================================================
# DEBUGGER CONFIGURATIONS
# ============================================================================

DEBUGGERS = {
    'gdb': {
        'name': 'GNU Debugger (GDB)',
        'command': 'gdb',
        'args': ['--args'],
        'platforms': ['Linux', 'MacOS', 'Windows'],
    },
    'ggdb': {
        'name': 'GDB (with extended info)',
        'command': 'gdb',
        'args': ['--args'],
        'platforms': ['Linux', 'MacOS', 'Windows'],
        'note': 'Executable must be compiled with -ggdb flag',
    },
    'lldb': {
        'name': 'LLVM Debugger (LLDB)',
        'command': 'lldb',
        'args': ['--'],
        'platforms': ['MacOS', 'Linux'],
    },
    'valgrind': {
        'name': 'Valgrind Memory Debugger',
        'command': 'valgrind',
        'args': ['--leak-check=full', '--show-leak-kinds=all', '--track-origins=yes'],
        'platforms': ['Linux', 'MacOS'],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_executable(workspace, config: str, platform: str, project_name: Optional[str] = None):
    """Find executable to run"""
    
    # Determine project
    if not project_name:
        project_name = workspace.startproject
    
    if not project_name:
        # Find first executable project
        for name, proj in workspace.projects.items():
            if proj.kind in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP]:
                project_name = name
                break
    
    if not project_name:
        Display.error("No executable project found")
        return None, None
    
    if project_name not in workspace.projects:
        Display.error(f"Project not found: {project_name}")
        return None, None
    
    project = workspace.projects[project_name]
    
    # Check if executable
    if project.kind not in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE]:
        Display.error(f"Project '{project_name}' is not executable (kind: {project.kind})")
        return None, None
    
    # Get executable path
    expander = VariableExpander(workspace, project, config, platform)
    
    # Get target directory and name
    target_dir = Path(expander.expand(project.targetdir))
    target_name = expander.expand(project.targetname) if project.targetname else project.name
    
    # Determine extension
    if platform == "Windows":
        executable = target_dir / f"{target_name}.exe"
    else:
        executable = target_dir / target_name
    
    if not executable.exists():
        Display.error(f"Executable not found: {executable}")
        Display.info("Build first with: jenga build")
        return None, None
    
    return executable, project


def check_debugger_available(debugger: str) -> bool:
    """Check if debugger is available on system"""
    debugger_info = DEBUGGERS.get(debugger)
    if not debugger_info:
        return False
    
    command = debugger_info['command']
    
    try:
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def run_with_debugger(executable: Path, debugger: str, args: List[str], workspace_dir: Path) -> int:
    """Run executable with specified debugger"""
    
    debugger_info = DEBUGGERS[debugger]
    
    # Check availability
    if not check_debugger_available(debugger):
        Display.error(f"{debugger_info['name']} not found on system")
        Display.info(f"Install {debugger} or use --debug=none")
        
        # Provide installation instructions
        if debugger in ['gdb', 'ggdb']:
            Display.info("\nInstall GDB:")
            Display.info("  Linux: sudo apt-get install gdb")
            Display.info("  MacOS: brew install gdb")
            Display.info("  Windows: Install MinGW-w64 or Cygwin")
        elif debugger == 'lldb':
            Display.info("\nInstall LLDB:")
            Display.info("  MacOS: Included with Xcode Command Line Tools")
            Display.info("  Linux: sudo apt-get install lldb")
        
        return 1
    
    # Build command
    cmd = [debugger_info['command']] + debugger_info['args'] + [str(executable)] + args
    
    Display.info(f"Starting {debugger_info['name']}...")
    Display.info(f"Command: {' '.join(cmd)}")
    
    if 'note' in debugger_info:
        Display.warning(f"Note: {debugger_info['note']}")
    
    print("=" * 70)
    
    try:
        result = subprocess.run(cmd, cwd=workspace_dir)
        print("=" * 70)
        
        if result.returncode == 0:
            Display.success("Debugger session completed")
        else:
            Display.warning(f"Debugger exited with code {result.returncode}")
        
        return result.returncode
        
    except KeyboardInterrupt:
        Display.warning("\nDebugger interrupted")
        return 130
    except Exception as e:
        Display.error(f"Error running debugger: {e}")
        return 1


def run_direct(executable: Path, args: List[str], workspace_dir: Path) -> int:
    """Run executable directly without debugger"""
    
    Display.info(f"Running: {executable}")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            [str(executable)] + args,
            cwd=workspace_dir
        )
        
        print("=" * 70)
        
        if result.returncode == 0:
            Display.success("Program completed successfully")
        else:
            Display.warning(f"Program exited with code {result.returncode}")
        
        return result.returncode
        
    except FileNotFoundError:
        Display.error(f"Could not execute: {executable}")
        return 127
    except KeyboardInterrupt:
        Display.warning("\nProgram interrupted")
        return 130
    except Exception as e:
        Display.error(f"Error running program: {e}")
        return 1


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def execute(options: dict) -> bool:
    """Execute run command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    # Extract options
    config = options.get("config", "Debug")
    platform = options.get("platform", "Windows")
    project_name = options.get("project")
    debugger = options.get("debug", "none")
    program_args = options.get("args", [])
    
    # Auto-detect platform if not specified
    if platform == "Windows":
        import platform as sys_platform
        if sys_platform.system() == "Linux":
            platform = "Linux"
        elif sys_platform.system() == "Darwin":
            platform = "MacOS"
    
    # Validate debugger
    if debugger not in ['none'] and debugger not in DEBUGGERS:
        Display.error(f"Unknown debugger: {debugger}")
        Display.info(f"Available: {', '.join(['none'] + list(DEBUGGERS.keys()))}")
        return False
    
    # Find executable
    executable, project = find_executable(workspace, config, platform, project_name)
    if not executable:
        return False
    
    # Display info
    Display.info(f"Project: {project.name}")
    Display.info(f"Configuration: {config}")
    Display.info(f"Platform: {platform}")
    Display.info(f"Executable: {executable}")
    
    if debugger != 'none':
        Display.info(f"Debugger: {DEBUGGERS[debugger]['name']}")
    
    if program_args:
        Display.info(f"Arguments: {' '.join(program_args)}")
    
    print()
    
    # Run
    workspace_dir = Path(workspace.location) if workspace.location else Path.cwd()
    
    if debugger == 'none':
        returncode = run_direct(executable, program_args, workspace_dir)
    else:
        returncode = run_with_debugger(executable, debugger, program_args, workspace_dir)
    
    return returncode == 0


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for command line"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run executable projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run default project
  jenga run
  
  # Run with GDB debugger
  jenga run --debug=gdb
  
  # Run with GGDB (extended debug info)
  jenga run --debug=ggdb
  
  # Run specific project
  jenga run --project MyApp
  
  # Run with arguments
  jenga run -- --verbose --config=test.json
  
  # Run Release build
  jenga run --config Release
  
  # Run with Valgrind memory check
  jenga run --debug=valgrind
  
Debuggers:
  none      - Run directly (default)
  gdb       - GNU Debugger
  ggdb      - GDB with extended debug info
  lldb      - LLVM Debugger (macOS/Linux)
  valgrind  - Memory debugger (Linux/macOS)
"""
    )
    
    parser.add_argument(
        '--config',
        default='Debug',
        help='Build configuration (default: Debug)'
    )
    
    parser.add_argument(
        '--platform',
        default='Windows',
        help='Target platform (default: Windows)'
    )
    
    parser.add_argument(
        '--project',
        help='Project name to run (default: startup project)'
    )
    
    parser.add_argument(
        '--debug',
        default='none',
        choices=['none', 'gdb', 'ggdb', 'lldb', 'valgrind'],
        help='Debugger to use (default: none)'
    )
    
    parser.add_argument(
        'args',
        nargs='*',
        help='Arguments to pass to the executable'
    )
    
    parsed = parser.parse_args()
    
    options = {
        'config': parsed.config,
        'platform': parsed.platform,
        'project': parsed.project,
        'debug': parsed.debug,
        'args': parsed.args,
    }
    
    success = execute(options)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()