#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Test Command
Dedicated command for running unit tests
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.variables import VariableExpander
from utils.display import Display


# ============================================================================
# TEST RUNNER CONFIGURATION
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
    'helgrind': {
        'name': 'Valgrind Thread Debugger',
        'command': 'valgrind',
        'args': ['--tool=helgrind'],
        'platforms': ['Linux', 'MacOS'],
    },
    'drd': {
        'name': 'Valgrind DRD Thread Debugger',
        'command': 'valgrind',
        'args': ['--tool=drd'],
        'platforms': ['Linux', 'MacOS'],
    },
}


# ============================================================================
# UNIT TEST SUPPORT FUNCTIONS
# ============================================================================

def find_test_project(workspace, project_name: Optional[str] = None) -> Optional[Dict]:
    """Find test project for a given project"""
    
    if project_name:
        # Look for specific project's tests
        test_project_name = f"{project_name}_Tests"
        if test_project_name in workspace.projects:
            project = workspace.projects[test_project_name]
            if hasattr(project, 'is_test') and project.is_test:
                return {
                    'name': test_project_name,
                    'project': project,
                    'parent': project.parent_project
                }
        # Also check if the name is already a test project
        elif project_name in workspace.projects:
            project = workspace.projects[project_name]
            if hasattr(project, 'is_test') and project.is_test:
                return {
                    'name': project_name,
                    'project': project,
                    'parent': project.parent_project
                }
    else:
        # Find default project's tests
        default_project = workspace.startproject
        if default_project:
            test_project_name = f"{default_project}_Tests"
            if test_project_name in workspace.projects:
                project = workspace.projects[test_project_name]
                if hasattr(project, 'is_test') and project.is_test:
                    return {
                        'name': test_project_name,
                        'project': project,
                        'parent': project.parent_project
                    }
    
    # Search all test projects
    test_projects = []
    for name, proj in workspace.projects.items():
        if hasattr(proj, 'is_test') and proj.is_test:
            test_projects.append({
                'name': name,
                'project': proj,
                'parent': proj.parent_project
            })
    
    if test_projects:
        if project_name:
            # Try to find test project by parent name
            for test_proj in test_projects:
                if test_proj['parent'] == project_name:
                    return test_proj
            # Or by exact name match
            for test_proj in test_projects:
                if test_proj['name'] == project_name:
                    return test_proj
        else:
            # Return first test project
            return test_projects[0]
    
    return None


def get_all_test_projects(workspace) -> List[Dict]:
    """Get all test projects in workspace"""
    test_projects = []
    for name, proj in workspace.projects.items():
        if hasattr(proj, 'is_test') and proj.is_test:
            test_projects.append({
                'name': name,
                'project': proj,
                'parent': proj.parent_project
            })
    return test_projects


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
        elif debugger in ['valgrind', 'helgrind', 'drd']:
            Display.info("\nInstall Valgrind:")
            Display.info("  Linux: sudo apt-get install valgrind")
            Display.info("  MacOS: brew install valgrind")
        
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
            Display.success("Tests completed successfully")
        else:
            Display.warning(f"Tests exited with code {result.returncode}")
        
        return result.returncode
        
    except FileNotFoundError:
        Display.error(f"Could not execute: {executable}")
        return 127
    except KeyboardInterrupt:
        Display.warning("\nTests interrupted")
        return 130
    except Exception as e:
        Display.error(f"Error running tests: {e}")
        return 1


def run_test_project(workspace, test_info: Dict, config: str, platform: str, 
                    debugger: str, test_args: List[str]) -> int:
    """Run a test project"""
    
    test_project = test_info['project']
    expander = VariableExpander(workspace, test_project, config, platform)
    
    # Get executable path
    target_dir = Path(expander.expand(test_project.targetdir))
    target_name = expander.expand(test_project.targetname) if test_project.targetname else test_info['name']
    
    if platform == "Windows":
        executable = target_dir / f"{target_name}.exe"
    else:
        executable = target_dir / target_name
    
    if not executable.exists():
        Display.error(f"Test executable not found: {executable}")
        Display.info("Build tests first with: jenga build")
        return 1
    
    # Add test-specific arguments from project configuration
    if hasattr(test_project, 'testoptions'):
        test_args = list(test_project.testoptions) + test_args
    
    Display.section(f"Running Tests: {test_info['name']}")
    Display.info(f"Parent Project: {test_info['parent']}")
    Display.info(f"Configuration: {config}")
    Display.info(f"Platform: {platform}")
    Display.info(f"Executable: {executable}")
    
    if debugger != 'none':
        Display.info(f"Debugger: {DEBUGGERS[debugger]['name']}")
    
    if test_args:
        Display.info(f"Arguments: {' '.join(test_args)}")
    
    print()
    
    # Run with debugger or directly
    workspace_dir = Path(workspace.location) if workspace.location else Path.cwd()
    
    if debugger == 'none':
        return run_direct(executable, test_args, workspace_dir)
    else:
        return run_with_debugger(executable, debugger, test_args, workspace_dir)


def run_all_tests(workspace, config: str, platform: str, 
                 debugger: str, test_args: List[str]) -> bool:
    """Run all test projects"""
    
    test_projects = get_all_test_projects(workspace)
    
    if not test_projects:
        Display.error("No test projects found in workspace")
        Display.info("Create tests using 'test' context in .jenga file")
        return False
    
    Display.info(f"Found {len(test_projects)} test project(s)")
    
    results = []
    for test_info in test_projects:
        result = run_test_project(workspace, test_info, config, platform, 
                                debugger, test_args)
        results.append((test_info['name'], result))
        
        # Add separator between test runs
        if test_info != test_projects[-1]:
            print("\n" + "=" * 70 + "\n")
    
    # Summary
    Display.section("Test Summary")
    passed = 0
    failed = 0
    
    for name, result in results:
        if result == 0:
            Display.success(f"✓ {name}: PASSED")
            passed += 1
        else:
            Display.error(f"✗ {name}: FAILED (code: {result})")
            failed += 1
    
    Display.info(f"\nTotal: {len(results)} test project(s)")
    Display.info(f"Passed: {passed}, Failed: {failed}")
    
    return failed == 0


def run_single_test(workspace, config: str, platform: str,
                   project_name: Optional[str], debugger: str, 
                   test_args: List[str]) -> bool:
    """Run a single test project"""
    
    test_info = find_test_project(workspace, project_name)
    if not test_info:
        Display.error(f"No test project found for '{project_name or workspace.startproject or 'default'}'")
        
        # Show available test projects
        test_projects = get_all_test_projects(workspace)
        if test_projects:
            Display.info("\nAvailable test projects:")
            for tp in test_projects:
                Display.info(f"  • {tp['name']} (parent: {tp['parent']})")
            Display.info("\nRun all tests with: jenga test")
        else:
            Display.info("\nNo test projects found. Create tests using 'test' context in .jenga file")
        
        return False
    
    result = run_test_project(workspace, test_info, config, platform, debugger, test_args)
    return result == 0


def list_test_projects(workspace) -> None:
    """List all test projects in workspace"""
    
    test_projects = get_all_test_projects(workspace)
    
    if not test_projects:
        Display.info("No test projects found in workspace")
        return
    
    Display.section("Test Projects")
    Display.info(f"Total: {len(test_projects)} test project(s)")
    
    for tp in test_projects:
        project = tp['project']
        Display.info(f"\n  • {tp['name']}:")
        Display.info(f"    Parent: {tp['parent']}")
        Display.info(f"    Location: {project.location}")
        Display.info(f"    Target: {project.targetdir}")
        
        if hasattr(project, 'testoptions') and project.testoptions:
            Display.info(f"    Options: {' '.join(project.testoptions)}")
        
        if project.testfiles:
            Display.info(f"    Test files: {', '.join(project.testfiles[:3])}")
            if len(project.testfiles) > 3:
                Display.info(f"      ... and {len(project.testfiles) - 3} more")


def build_test_projects(workspace, config: str, platform: str) -> bool:
    """Build all test projects"""
    from core.build import Compiler
    
    test_projects = get_all_test_projects(workspace)
    
    if not test_projects:
        Display.error("No test projects to build")
        return False
    
    Display.info(f"Building {len(test_projects)} test project(s)...")
    
    compiler = Compiler(workspace, config, platform, jobs=None, use_cache=True)
    
    success = True
    for test_info in test_projects:
        Display.section(f"Building: {test_info['name']}")
        if not compiler.compile_project(test_info['project']):
            success = False
            Display.error(f"Failed to build {test_info['name']}")
        else:
            Display.success(f"Built {test_info['name']}")
    
    return success


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def execute(options: dict) -> bool:
    """Execute test command"""
    
    # Load workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    # Extract options
    config = options.get("config", "Debug")
    platform = options.get("platform", "Windows")
    project_name = options.get("project")
    debugger = options.get("debug", "none")
    test_args = options.get("args", [])
    action = options.get("action", "run")  # run, list, build
    
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
    
    # Handle different actions
    if action == "list":
        list_test_projects(workspace)
        return True
    elif action == "build":
        return build_test_projects(workspace, config, platform)
    else:  # action == "run"
        if project_name == "all" or not project_name:
            # Run all tests
            return run_all_tests(workspace, config, platform, debugger, test_args)
        else:
            # Run single test
            return run_single_test(workspace, config, platform, project_name, debugger, test_args)


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point for command line"""
    
    parser = argparse.ArgumentParser(
        description="Jenga Test Command - Run unit tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all unit tests in workspace
  jenga test
  
  # Run tests for specific project
  jenga test --project MyApp
  
  # Run tests with debugger
  jenga test --debug=gdb
  
  # Run tests in Release configuration
  jenga test --config Release
  
  # Run tests with custom arguments
  jenga test -- --verbose --filter=Math*
  
  # List all test projects
  jenga test --list
  
  # Build all test projects
  jenga test --build
  
  # Run tests with Valgrind memory check
  jenga test --debug=valgrind
  
  # Run tests with thread debugging
  jenga test --debug=helgrind
  
  # Run tests on specific platform
  jenga test --platform Linux
  
Test Runner Arguments (passed to unit test executable):
  --help, -h              Show help
  --verbose, -v           Verbose output
  --quiet, -q             Quiet output
  --stop-on-failure, -f   Stop on first failure
  --no-colors             Disable colored output
  --no-progress           Disable progress bar
  --debug                 Enable debug mode
  --filter=PATTERN        Run tests matching pattern
  --exclude=PATTERN       Exclude tests matching pattern
  --parallel[=N]          Run tests in parallel (N threads)
  --repeat=N              Repeat tests N times
  --report=FILE           Generate report file

Debuggers:
  none      - Run directly (default)
  gdb       - GNU Debugger
  ggdb      - GDB with extended debug info
  lldb      - LLVM Debugger (macOS/Linux)
  valgrind  - Memory debugger (Linux/macOS)
  helgrind  - Thread debugger (Linux/macOS)
  drd       - DRD thread debugger (Linux/macOS)
"""
    )
    
    # Test selection
    parser.add_argument(
        '--project',
        default='all',
        help='Project name to test (default: all projects)'
    )
    
    # Build configuration
    parser.add_argument(
        '--config',
        default='Debug',
        choices=['Debug', 'Release', 'Development', 'Shipping'],
        help='Build configuration (default: Debug)'
    )
    
    parser.add_argument(
        '--platform',
        default='Windows',
        choices=['Windows', 'Linux', 'MacOS', 'Android', 'iOS', 'Emscripten'],
        help='Target platform (default: Windows)'
    )
    
    # Debugger options
    parser.add_argument(
        '--debug',
        default='none',
        choices=['none', 'gdb', 'ggdb', 'lldb', 'valgrind', 'helgrind', 'drd'],
        help='Debugger to use (default: none)'
    )
    
    # Actions
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        '--list',
        action='store_const',
        const='list',
        dest='action',
        help='List all test projects'
    )
    
    action_group.add_argument(
        '--build',
        action='store_const',
        const='build',
        dest='action',
        help='Build all test projects'
    )
    
    action_group.add_argument(
        '--run',
        action='store_const',
        const='run',
        dest='action',
        help='Run tests (default)'
    )
    
    # Test runner arguments
    parser.add_argument(
        'args',
        nargs='*',
        help='Arguments to pass to the test runner'
    )
    
    parsed = parser.parse_args()
    
    # Default action is 'run'
    if parsed.action is None:
        parsed.action = 'run'
    
    options = {
        'config': parsed.config,
        'platform': parsed.platform,
        'project': parsed.project if parsed.project != 'all' else None,
        'debug': parsed.debug,
        'action': parsed.action,
        'args': parsed.args,
    }
    
    success = execute(options)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()