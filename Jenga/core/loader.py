#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Configuration Loader
Loads and executes .jenga files
"""

import sys
from pathlib import Path
from typing import Optional
import importlib.util
import re

# Fix imports to work from any context
try:
    from .api import get_current_workspace, reset_state, _current_project, _current_workspace
except ImportError:
    from core.api import get_current_workspace, reset_state
    try:
        from core.api import _current_project, _current_workspace
    except ImportError:
        _current_project = None
        _current_workspace = None

try:
    from ..utils.display import Display
except ImportError:
    from utils.display import Display


class ConfigurationLoader:
    """Loads .jenga configuration files"""
    
    @staticmethod
    def find_jenga_file(start_dir: str = ".") -> Optional[Path]:
        """Find .jenga file in current or parent directories"""
        current = Path(start_dir).resolve()
        
        # Search in current and parent directories
        for directory in [current] + list(current.parents):
            for nken_file in directory.glob("*.jenga"):
                return nken_file
        
        return None
    
    @staticmethod
    def comment_jenga_imports(jenga_code: str) -> str:
        """
        Comment out all jenga imports to avoid import errors
        Handles various import formats
        """
        lines = jenga_code.split('\n')
        commented_lines = []
        
        for line in lines:
            # Skip already commented lines
            stripped = line.lstrip()
            if stripped.startswith('#'):
                commented_lines.append(line)
                continue
            
            # Pattern to detect various jenga imports
            patterns = [
                # from XXX.jenga.core.api import xxx
                r'^\s*from\s+(\w+\.)*jenga\.',
                # from jenga.core.api import xxx  
                r'^\s*from\s+jenga\.',
                # import XXX.jenga.core.api as xxx
                r'^\s*import\s+(\w+\.)*jenga\.',
                # import jenga.core.api as xxx
                r'^\s*import\s+jenga\.',
                # from XXX.jenga import xxx
                r'^\s*from\s+(\w+\.)*jenga\s+import\s+',
                # import XXX.jenga as xxx
                r'^\s*import\s+(\w+\.)*jenga\s+as\s+',
                # import jenga as xxx
                r'^\s*import\s+jenga\s+as\s+',
                # import XXX.jenga
                r'^\s*import\s+(\w+\.)*jenga(\s+|$)',
                # import jenga
                r'^\s*import\s+jenga(\s+|$)',
            ]
            
            is_jenga_import = False
            for pattern in patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_jenga_import = True
                    break
            
            if is_jenga_import:
                # Check if it's a multi-line import (ends with backslash or parenthesis)
                if line.rstrip().endswith('\\') or '(' in line:
                    # It's a multi-line import, we need to handle it differently
                    commented_lines.append(f"# {line}  # Auto-commented by Jenga loader")
                    # We'll need to comment subsequent lines until the import ends
                    # This is handled by the multi-line logic below
                else:
                    # Single line import, just comment it
                    commented_lines.append(f"# {line}  # Auto-commented by Jenga loader")
            else:
                commented_lines.append(line)
        
        # Now handle multi-line imports by checking for continued lines
        final_lines = []
        in_multiline_import = False
        
        for line in commented_lines:
            stripped = line.lstrip()
            
            # Check if this line starts a multi-line import that we've commented
            if stripped.startswith('#') and any(pattern in line for pattern in [
                'from jenga', 'import jenga', 'jenga.core', 'jenga import'
            ]):
                # Check if it continues on next line
                if line.rstrip().endswith('\\'):
                    in_multiline_import = True
                    final_lines.append(line)
                    continue
                elif '(' in line and not ')' in line:
                    # Multi-line import with parentheses
                    in_multiline_import = True
                    final_lines.append(line)
                    continue
            
            # If we're in a multi-line import, continue commenting
            if in_multiline_import:
                if not stripped.startswith('#'):
                    final_lines.append(f"# {line}  # Auto-commented by Jenga loader")
                else:
                    final_lines.append(line)
                
                # Check if this ends the multi-line import
                if ')' in line or not line.rstrip().endswith('\\'):
                    in_multiline_import = False
            else:
                final_lines.append(line)
        
        return '\n'.join(final_lines)
    
    @staticmethod
    def load(file_path: str = None) -> Optional[object]:
        """
        Load a .jenga configuration file
        Returns the workspace object
        """
        
        # Reset global state
        reset_state()
        
        # Find .jenga file
        if file_path is None:
            nken_path = ConfigurationLoader.find_jenga_file()
            if nken_path is None:
                Display.error("No .jenga file found in current directory or parents")
                return None
        else:
            nken_path = Path(file_path)
            if not nken_path.exists():
                Display.error(f"Configuration file not found: {file_path}")
                return None
        
        Display.info(f"Loading configuration: {nken_path.name}")
        
        try:
            # Get absolute path
            nken_path = nken_path.resolve()
            
            # Change to the directory containing the .jenga file
            original_dir = Path.cwd()
            nken_dir = nken_path.parent
            
            # Add the directory to Python path
            sys.path.insert(0, str(nken_dir))
            
            # Import the Tools.core module to make API available
            tools_dir = Path(__file__).parent.parent
            if str(tools_dir) not in sys.path:
                sys.path.insert(0, str(tools_dir))
            
            # Import core.api to get API functions
            try:
                import core.api as api
            except ImportError:
                # Fallback: try absolute import from Tools
                sys.path.insert(0, str(tools_dir.parent))
                from Tools import core
                api = core.api
            
            # Read the .jenga file with UTF-8 encoding
            with open(nken_path, 'r', encoding='utf-8') as f:
                jenga_code = f.read()
            
            # Comment out all jenga imports
            jenga_code = ConfigurationLoader.comment_jenga_imports(jenga_code)
            
            # Also remove any other potential problematic imports
            # This handles edge cases like relative imports that might conflict
            additional_patterns = [
                # Remove any 'from .api import' lines (these might be leftover from templates)
                (r'^\s*from\s+\.api\s+import\s+.*$', r'# \g<0>  # Auto-commented by Jenga loader'),
                # Remove 'from api import' 
                (r'^\s*from\s+api\s+import\s+.*$', r'# \g<0>  # Auto-commented by Jenga loader'),
                # Remove 'import api'
                (r'^\s*import\s+api(\s+|$)', r'# \g<0>  # Auto-commented by Jenga loader'),
            ]
            
            for pattern, replacement in additional_patterns:
                jenga_code = re.sub(pattern, replacement, jenga_code, flags=re.MULTILINE)
            
            # Create execution environment with API module
            exec_globals = {
                '__file__': str(nken_path),
                '__name__': '__main__',
                '__builtins__': __builtins__,
            }
            
            # Import the API module into the execution context
            # This way, when .jenga calls workspace(), it modifies api._current_workspace
            exec_globals.update({name: getattr(api, name) for name in dir(api) if not name.startswith('_')})
            
            # Also add commonly used functions from api to avoid NameError
            # Add aliases for commonly used API functions
            api_aliases = {
                'workspace': api.workspace,
                'project': api.project,
                'toolchain': api.toolchain,
                'filter': api.filter,
                'consoleapp': api.consoleapp,
                'windowedapp': api.windowedapp,
                'staticlib': api.staticlib,
                'sharedlib': api.sharedlib,
                'language': api.language,
                'cppdialect': api.cppdialect,
                'configurations': api.configurations,
                'platforms': api.platforms,
                'startproject': api.startproject,
                'files': api.files,
                'excludefiles': api.excludefiles,
                'includedirs': api.includedirs,
                'libdirs': api.libdirs,
                'links': api.links,
                'dependson': api.dependson,
                'dependfiles': api.dependfiles,
                'defines': api.defines,
                'objdir': api.objdir,
                'targetdir': api.targetdir,
                'targetname': api.targetname,
                'optimize': api.optimize,
                'symbols': api.symbols,
                'cppcompiler': api.cppcompiler,
                'ccompiler': api.ccompiler,
                'cxxflags': api.cxxflags,
                'prebuild': api.prebuild,
                'postbuild': api.postbuild,
                'prelink': api.prelink,
                'postlink': api.postlink,
                'usetoolchain': api.usetoolchain,
                'encoding': api.encoding,
            }
            
            exec_globals.update(api_aliases)
            
            # Add the API module itself
            exec_globals['api'] = api
            
            # Execute the .jenga file
            try:
                exec(jenga_code, exec_globals)
            except NameError as e:
                Display.error(f"NameError in configuration file: {e}")
                Display.info("This might be due to missing imports. The following API functions are available:")
                Display.info("  workspace(), project(), toolchain(), filter(), configurations(), platforms()")
                Display.info("  consoleapp(), staticlib(), sharedlib(), language(), cppdialect()")
                Display.info("  files(), includedirs(), defines(), optimize(), symbols()")
                Display.info("  See documentation for complete list of available functions.")
                return None
            except Exception as e:
                Display.error(f"Error executing configuration file: {e}")
                import traceback
                traceback.print_exc()
                return None
            
            # Now get workspace from api module (not from exec_globals)
            workspace = api.get_current_workspace()
            
            if workspace is None:
                # ✅ SOLUTION: Check if a standalone project was defined
                # Access the global variable directly from the api module
                current_proj = getattr(api, '_current_project', None)
                
                if current_proj is not None:
                    Display.info(f"Standalone project detected: {current_proj.name}")
                    
                    # Create automatic workspace for standalone project
                    workspace = api.Workspace(name=f"Auto_{nken_path.stem}")
                    workspace.location = str(nken_dir)
                    workspace.configurations = ["Debug", "Release", "Dist"]
                    workspace.platforms = ["Windows", "Linux", "MacOS"]
                    
                    # Add the standalone project to the workspace
                    workspace.projects[current_proj.name] = current_proj
                    
                    # Set project location if not already set
                    if not current_proj.location or current_proj.location == ".":
                        current_proj.location = str(nken_dir)
                    
                    # Create default toolchain
                    default_tc = api.Toolchain(name="default", compiler="clang++")
                    default_tc.cppcompiler = "clang++"
                    default_tc.ccompiler = "clang"
                    default_tc.linker = "clang++"
                    default_tc.archiver = "ar"
                    workspace.toolchains["default"] = default_tc
                    
                    # Assign toolchain to project if not set
                    if not current_proj.toolchain:
                        current_proj.toolchain = "default"
                    
                    Display.success(f"Auto-created workspace '{workspace.name}' for standalone project '{current_proj.name}'")
                else:
                    Display.error("No workspace or project defined in configuration file")
                    Display.info("Your .jenga file must contain either:")
                    Display.info("  1. A workspace: with workspace('YourName'): ...")
                    Display.info("  2. A standalone project: with project('YourName'): ...")
                    Display.info("")
                    Display.info("Debug info:")
                    Display.info(f"  - File: {nken_path}")
                    Display.info(f"  - api._current_project: {getattr(api, '_current_project', 'NOT FOUND')}")
                    Display.info(f"  - api._current_workspace: {getattr(api, '_current_workspace', 'NOT FOUND')}")
                    Display.info("")
                    Display.info("Common issues:")
                    Display.info("  - Missing 'with workspace(...)' or 'with project(...)' statement")
                    Display.info("  - API functions called outside context")
                    Display.info("  - Syntax errors in the .jenga file")
                    return None
            
            # Set workspace location to the directory containing .jenga file
            if not workspace.location:
                workspace.location = str(nken_dir)
            
            # Validate workspace has at least one toolchain
            if not workspace.toolchains:
                Display.warning("No toolchains defined - creating default toolchain")
                # Create a default toolchain
                default_tc = api.Toolchain(name="default", compiler="clang++")
                default_tc.cppcompiler = "clang++"
                default_tc.ccompiler = "clang"
                default_tc.linker = "clang++"
                default_tc.archiver = "ar"
                workspace.toolchains["default"] = default_tc
            
            Display.success(f"Workspace '{workspace.name}' loaded with {len(workspace.projects)} project(s)")
            
            return workspace
            
        except Exception as e:
            Display.error(f"Error loading configuration: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            # Restore original directory
            if 'original_dir' in locals():
                import os
                os.chdir(original_dir)


def load_workspace(file_path: str = None) -> Optional[object]:
    """Convenience function to load workspace"""
    return ConfigurationLoader.load(file_path)


if __name__ == "__main__":
    # Test the loader
    workspace = load_workspace()
    if workspace:
        print(f"Loaded workspace: {workspace.name}")
        print(f"Projects: {list(workspace.projects.keys())}")