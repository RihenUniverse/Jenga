#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Command Registry
Manages available commands
"""

from typing import Dict, Callable
from pathlib import Path
import importlib


class CommandRegistry:
    """Registry of available build commands"""
    
    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self._load_commands()
    
    def _load_commands(self):
        """Load all commands from Commands directory"""
        
        commands_dir = Path(__file__).parent.parent / "Commands"
        
        if not commands_dir.exists():
            return
        
        # Import all command modules
        for cmd_file in commands_dir.glob("*.py"):
            if cmd_file.name.startswith("_"):
                continue
            
            module_name = cmd_file.stem
            
            try:
                # Import module
                module = importlib.import_module(f"Commands.{module_name}")
                
                # Look for execute function
                if hasattr(module, "execute"):
                    self.commands[module_name] = module.execute
                
            except Exception as e:
                print(f"Warning: Failed to load command '{module_name}': {e}")
    
    def execute(self, command: str, options: dict) -> bool:
        """Execute a command"""
        
        if command not in self.commands:
            return False
        
        try:
            return self.commands[command](options)
        except Exception as e:
            print(f"Error executing command '{command}': {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_commands(self) -> list:
        """List available commands"""
        return sorted(self.commands.keys())
