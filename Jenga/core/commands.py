#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Command Registry
Manages available commands
"""

from typing import Dict, Callable
from pathlib import Path
import importlib
import sys


class CommandRegistry:
    """Registry of available build commands"""
    
    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self._load_builtin_commands()
        self._load_command_modules()
    
    def _load_builtin_commands(self):
        """Load built-in commands that don't have separate modules"""
        
        # Version command
        self.commands["version"] = self._version_command
        
        # Help command
        self.commands["help"] = self._help_command
    
    def _load_command_modules(self):
        """Load all commands from Commands directory"""
        
        commands_dir = Path(__file__).parent.parent / "Commands"
        
        if not commands_dir.exists():
            return
        
        # Import all command modules
        for cmd_file in commands_dir.glob("*.py"):
            if cmd_file.name.startswith("_") or cmd_file.name == "create.py":
                continue
            
            module_name = cmd_file.stem
            
            try:
                # Import module
                module = importlib.import_module(f"Commands.{module_name}")
                
                # Look for execute function
                if hasattr(module, "execute"):
                    self.commands[module_name] = module.execute
                elif hasattr(module, "main"):
                    self.commands[module_name] = module.main
                
            except Exception as e:
                print(f"Warning: Failed to load command '{module_name}': {e}")
                import traceback
                traceback.print_exc()
    
    def _version_command(self, options: dict) -> bool:
        """Handle version command"""
        from Jenga.jenga import __version__
        from utils.display import Display
        
        Display.info(f"Jenga Build System v{__version__}")
        Display.info(f"Copyright © 2025 Rihen")
        Display.info(f"License: Proprietary")
        return True
    
    def _help_command(self, options: dict) -> bool:
        """Handle help command"""
        from Jenga.jenga import print_help
        print_help()
        return True
    
    def execute(self, command: str, options: dict) -> bool:
        """Execute a command"""
        
        if command not in self.commands:
            # Try to check if it's a create subcommand
            if command.startswith("create"):
                return self._handle_create_command(command, options)
            return False
        
        try:
            return self.commands[command](options)
        except Exception as e:
            from utils.display import Display
            Display.error(f"Error executing command '{command}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _handle_create_command(self, command: str, options: dict) -> bool:
        """Handle create command and its subcommands"""
        from Commands.create import execute
        
        # Parse create subcommand
        parts = command.split()
        if len(parts) < 2:
            # Just "jenga create" - show help
            sys.argv = ["create", "--help"]
        else:
            # "jenga create workspace" -> ["create", "workspace", ...]
            sys.argv = ["create"] + parts[1:]
        
        try:
            # Execute create command
            return execute(sys.argv[1:]) == 0  # Convert return code to boolean
        except SystemExit as e:
            return e.code == 0
        except Exception as e:
            from utils.display import Display
            Display.error(f"Error in create command: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_commands(self) -> list:
        """List available commands"""
        commands = list(self.commands.keys())
        
        # Add create subcommands
        create_subcommands = ["workspace", "project", "file"]
        commands.extend([f"create {sub}" for sub in create_subcommands])
        
        return sorted(commands)