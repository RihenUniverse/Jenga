#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Main Entry Point
Cross-platform build system with direct compilation support
"""

import sys
import os
from pathlib import Path

# Add Tools directory to Python path
JENGA_DIR = Path(__file__).parent
sys.path.insert(0, str(JENGA_DIR))

from core.commands import CommandRegistry
from utils.display import Display, Colors
from utils.reporter import Reporter

__version__ = "1.1.0"  # Mettre à jour avec votre version actuelle


def print_banner():
    """Print Jenga banner with exact design"""
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗
║{Colors.RESET}                                                                  {Colors.CYAN}║
║{Colors.RESET}           {Colors.BOLD}{Colors.MAGENTA}     ██╗███████╗███╗   ██╗ ██████╗  █████╗{Colors.RESET}             {Colors.CYAN}║
║{Colors.RESET}           {Colors.BOLD}{Colors.MAGENTA}     ██║██╔════╝████╗  ██║██╔════╝ ██╔══██╗{Colors.RESET}            {Colors.CYAN}║
║{Colors.RESET}           {Colors.BOLD}{Colors.MAGENTA}     ██║█████╗  ██╔██╗ ██║██║  ███╗███████║{Colors.RESET}            {Colors.CYAN}║
║{Colors.RESET}           {Colors.BOLD}{Colors.MAGENTA}██   ██║██╔══╝  ██║╚██╗██║██║   ██║██╔══██║{Colors.RESET}            {Colors.CYAN}║
║{Colors.RESET}           {Colors.BOLD}{Colors.MAGENTA}╚█████╔╝███████╗██║ ╚████║╚██████╔╝██║  ██║{Colors.RESET}            {Colors.CYAN}║
║{Colors.RESET}           {Colors.BOLD}{Colors.MAGENTA} ╚════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝{Colors.RESET}            {Colors.CYAN}║
║{Colors.RESET}                                                                  {Colors.CYAN}║
║{Colors.RESET}             {Colors.BOLD}Multi-platform C/C++ Build System v{__version__}{Colors.RESET}             {Colors.CYAN}║
║{Colors.RESET}                                                                  {Colors.CYAN}║
╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)


def print_version():
    """Print version information"""
    version_info = f"""
{Colors.BOLD}Jenga Build System{Colors.RESET}
Version: {Colors.GREEN}{__version__}{Colors.RESET}
Python: {sys.version.split()[0]}
Platform: {sys.platform}
Copyright © 2025 Rihen
License: Proprietary
"""
    print(version_info)


def print_help():
    """Print help message"""
    help_text = f"""
{Colors.BOLD}Usage:{Colors.RESET} jenga [command] [options]

{Colors.BOLD}Available Commands:{Colors.RESET}
  build      - Build the workspace/project
  rebuild    - Clean and build the workspace/project
  clean      - Clean build artifacts
  run        - Run the built executable
  test       - Run the built executable with test framework
  package    - Package the application (APK, AAB, ZIP, DMG, etc.)
  sign       - Sign the application (Android APK, iOS IPA, etc.)
  keygen     - Generate keystore for signing
  info       - Display workspace/project information
  create     - Create workspaces, projects, and files
  version    - Show version information
  help       - Show this help message

{Colors.BOLD}Create Subcommands:{Colors.RESET}
  create workspace    - Create a new workspace
  create project      - Create a new project
  create file         - Create a source file

{Colors.BOLD}Options:{Colors.RESET}
  --config <name>     - Specify configuration (Debug, Release, Dist)
  --platform <name>   - Specify platform (Windows, Linux, MacOS, Android, iOS, Emscripten)
  --project <name>    - Specify project to build
  --toolchain <name>  - Specify toolchain to use
  --jobs <N>          - Number of parallel jobs (default: CPU count)
  --verbose           - Enable verbose output
  --no-cache          - Disable compilation cache
  --version           - Show version information
  --help              - Show this help message

{Colors.BOLD}Examples:{Colors.RESET}
  jenga --version
  jenga build --config Release
  jenga create workspace MyGame
  jenga create project Engine --type staticlib
  jenga create file Player --type class
  jenga rebuild --project MyApp --jobs 8
  jenga run --config Debug
  jenga clean
  jenga info
"""
    print(help_text)


def parse_options(args):
    """Parse command line options"""
    import platform as plat
    
    # Detect native platform if not specified
    def detect_platform():
        system = plat.system()
        if system == "Windows":
            return "Windows"
        elif system == "Linux":
            return "Linux"
        elif system == "Darwin":
            return "MacOS"
        else:
            return "Linux"  # Default
    
    options = {
        "platform": detect_platform(),  # Auto-detect by default
        "config": "Debug",  # Default configuration
    }
    
    i = 0
    
    while i < len(args):
        arg = args[i]
        
        if arg.startswith("--"):
            option_name = arg[2:]
            
            # Boolean flags
            if option_name in ["verbose", "no-cache"]:
                options[option_name.replace("-", "_")] = True
                i += 1
            # Options with values
            elif i + 1 < len(args):
                value = args[i + 1]
                # Convertir les valeurs booléennes si nécessaire
                if option_name in ["verbose"]:
                    options[option_name.replace("-", "_")] = value.lower() in ["true", "yes", "1", "on"]
                else:
                    options[option_name.replace("-", "_")] = value
                i += 2
            else:
                Display.warning(f"Option {arg} requires a value")
                i += 1
        else:
            i += 1
    
    # Show detected platform if not explicitly set
    if "--platform" not in args:
        Display.info(f"Auto-detected platform: {options['platform']}")
    
    return options


def main():
    """Main entry point"""
    args = sys.argv[1:]
    print_banner()
    
    # No arguments - show help
    if not args:
        print_help()
        return 0
    
    command = args[0]
    
    # Handle version command
    if command in ["--version", "-v", "version"]:
        print_version()
        return 0
    
    # Handle help command
    if command in ["help", "-h", "--help"]:
        print_help()
        return 0
    
    # Handle create command separately
    if command == "create":
        try:
            from Commands.create import execute
            return execute(args[1:])
        except ImportError as e:
            Display.error(f"Failed to load create command: {e}")
            return 1
    
    # Parse options
    options = parse_options(args[1:])

    # Handle install command separately
    if command == "install":
        try:
            from Commands.install import execute
            return execute(options)
        except ImportError as e:
            Display.error(f"Failed to load install command: {e}")
            return 1

    # Handle docs command separately
    if command == "docs":
        try:
            from Commands.docs import execute
            return execute(args[1:])  # Passer les arguments directement
        except ImportError as e:
            Display.error(f"Failed to load docs command: {e}")
            return 1
    
    # Initialize reporter - S'assurer que verbose est un booléen
    verbose_value = options.get("verbose", False)
    # Si c'est une chaîne, la convertir en booléen
    if isinstance(verbose_value, str):
        Reporter.verbose = verbose_value.lower() in ["true", "yes", "1", "on"]
    else:
        Reporter.verbose = bool(verbose_value)
    
    try:
        # Load command registry
        registry = CommandRegistry()
        
        # Execute command
        if command in registry.commands:
            result = registry.execute(command, options)
            return 0 if result else 1
        else:
            Display.error(f"Unknown command: {command}")
            print_help()
            return 1
            
    except KeyboardInterrupt:
        Display.warning("\nBuild interrupted by user")
        return 130
    except Exception as e:
        Display.error(f"Fatal error: {e}")
        if options.get("verbose"):
            import traceback
            traceback.print_exc()
        return 1