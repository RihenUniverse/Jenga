#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Build System Core
Handles compilation with parallel execution and caching
"""

import os
import sys
import hashlib
import json
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

try:
    from .api import Project, ProjectKind, Workspace, Optimization
    from .variables import VariableExpander, resolve_file_list
except ImportError:
    from core.api import Project, ProjectKind, Workspace, Optimization
    from core.variables import VariableExpander, resolve_file_list

try:
    from ..utils.display import Display, Colors
    from ..utils.reporter import Reporter
except ImportError:
    from utils.display import Display, Colors
    from utils.reporter import Reporter


@dataclass
class CompilationUnit:
    """Represents a single file to compile"""
    source_file: str
    object_file: str
    include_dirs: List[str]
    defines: List[str]
    flags: List[str]
    compiler: str
    is_cpp: bool


@dataclass
class BuildCache:
    """Build cache for incremental compilation"""
    cache_dir: Path
    cache_data: Dict[str, Dict] = None
    
    def __post_init__(self):
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cbuild.json"
        self.load()
    
    def load(self):
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache_data = json.load(f)
            except:
                self.cache_data = {}
        else:
            self.cache_data = {}
    
    def save(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
        except Exception as e:
            Display.warning(f"Failed to save cache: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate hash - using only mtime for speed"""
        try:
            path = Path(file_path)
            if not path.exists():
                return ""
            
            # Use only mtime for much faster checks
            # Full content hash only if mtime matches but we suspect changes
            mtime = path.stat().st_mtime
            size = path.stat().st_size
            
            hasher = hashlib.sha256()
            hasher.update(f"{mtime}:{size}".encode())
            
            return hasher.hexdigest()
        except:
            return ""
    
    def needs_rebuild(self, source_file: str, object_file: str, includes: List[str], 
                     defines: List[str], flags: List[str]) -> bool:
        """Check if source file needs to be recompiled"""
        
        # Object file doesn't exist
        if not Path(object_file).exists():
            return True
        
        # Get cache key
        cache_key = source_file
        
        # Not in cache
        if cache_key not in self.cache_data:
            return True
        
        cached = self.cache_data[cache_key]
        
        # Check source file hash
        current_hash = self.get_file_hash(source_file)
        if cached.get("source_hash") != current_hash:
            return True
        
        # Check if compilation options changed
        current_options = {
            "defines": sorted(defines),
            "flags": sorted(flags),
            "includes": sorted(includes)
        }
        
        if cached.get("options") != current_options:
            return True
        
        # Check included headers (if tracked)
        if "includes_hash" in cached:
            # For now, we'll do a simple check
            # A more sophisticated system would track all #include files
            pass
        
        return False
    
    def update(self, source_file: str, object_file: str, includes: List[str],
              defines: List[str], flags: List[str]):
        """Update cache entry for a file"""
        cache_key = source_file
        
        self.cache_data[cache_key] = {
            "source_hash": self.get_file_hash(source_file),
            "object_file": object_file,
            "options": {
                "defines": sorted(defines),
                "flags": sorted(flags),
                "includes": sorted(includes)
            },
            "timestamp": time.time()
        }


class Compiler:
    """Handles compilation tasks"""
    
    def __init__(self, workspace: Workspace, config: str, platform: str, 
                 jobs: int = None, use_cache: bool = True):
        self.workspace = workspace
        self.config = config
        self.platform = platform
        self.jobs = jobs or multiprocessing.cpu_count()
        self.use_cache = use_cache
        
        # Initialize cache
        cache_dir = Path(workspace.location) / ".cjenga"
        self.cache = BuildCache(cache_dir) if use_cache else None
        
        # Statistics
        self.stats = {
            "compiled": 0,
            "cached": 0,
            "failed": 0,
            "linked": 0
        }
    
    def compile_project(self, project: Project, toolchain_name: str = "default") -> bool:
        """Compile a project"""
        
        Reporter.section(f"Building project: {project.name}")
        
        # Get toolchain - use project-specific toolchain if specified
        if project.toolchain:
            toolchain_name = project.toolchain
        
        if toolchain_name not in self.workspace.toolchains:
            Display.error(f"Toolchain '{toolchain_name}' not found")
            return False
        
        toolchain = self.workspace.toolchains[toolchain_name]
        
        # Create variable expander
        expander = VariableExpander(self.workspace, project, self.config, self.platform)
        
        # Execute pre-build commands
        if project.prebuildcommands:
            Reporter.info("Executing pre-build commands...")
            if not self._execute_commands(project.prebuildcommands, expander):
                Display.error("Pre-build commands failed")
                return False
        
        # Resolve dependencies
        all_include_dirs, all_lib_dirs, all_links = self._resolve_dependencies(project, expander)
        
        # Resolve file lists
        source_files = self._resolve_source_files(project, expander)
        
        if not source_files:
            Display.warning(f"No source files found for project {project.name} -> {project.location}")
            # Still execute post-build for libraries that might just copy headers
            if project.postbuildcommands:
                Reporter.info("Executing post-build commands...")
                self._execute_commands(project.postbuildcommands, expander)
            return True
        
        Reporter.info(f"Found {len(source_files)} source file(s)")
        
        # Create output directories
        obj_dir = Path(expander.expand(project.objdir))
        target_dir = Path(expander.expand(project.targetdir))
        
        obj_dir.mkdir(parents=True, exist_ok=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Get compiler settings
        defines = self._get_defines(project, toolchain, expander)
        flags = self._get_compiler_flags(project, toolchain, expander)
        
        # Create compilation units
        units = []
        for src_file in source_files:
            src_path = Path(src_file)
            obj_file = obj_dir / src_path.with_suffix(".o").name
            
            is_cpp = src_path.suffix in ['.cpp', '.cc', '.cxx', '.hpp', '.inl']
            compiler = self._get_compiler(toolchain, is_cpp)
            
            unit = CompilationUnit(
                source_file=src_file,
                object_file=str(obj_file),
                include_dirs=all_include_dirs,
                defines=defines,
                flags=flags,
                compiler=compiler,
                is_cpp=is_cpp
            )
            units.append(unit)
        
        # Filter units that need compilation (cache check)
        units_to_compile = []
        for unit in units:
            if self.cache and not self.cache.needs_rebuild(
                unit.source_file, unit.object_file, unit.include_dirs, 
                unit.defines, unit.flags
            ):
                self.stats["cached"] += 1
                Reporter.detail(f"[CACHED] {Path(unit.source_file).name}")
            else:
                units_to_compile.append(unit)
        
        if units_to_compile:
            Reporter.info(f"Compiling {len(units_to_compile)} file(s) ({self.stats['cached']} cached)")
            
            # Compile in parallel
            if not self._compile_units_parallel(units_to_compile):
                return False
        else:
            Reporter.success("All files up to date")
        
        # Execute pre-link commands
        if project.prelinkcommands:
            Reporter.info("Executing pre-link commands...")
            if not self._execute_commands(project.prelinkcommands, expander):
                Display.error("Pre-link commands failed")
                return False
        
        # Link
        object_files = [unit.object_file for unit in units]
        output_file = self._get_output_path(project, target_dir, expander)
        
        if not self._link(project, toolchain, object_files, output_file, 
                         all_lib_dirs, all_links, expander):
            return False
        
        # Execute post-link commands
        if project.postlinkcommands:
            Reporter.info("Executing post-link commands...")
            if not self._execute_commands(project.postlinkcommands, expander):
                Display.error("Post-link commands failed")
                return False
        
        Reporter.success(f"Built: {output_file}")
        
        # Copy dependency DLLs/SOs automatically for executables
        if project.kind in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP]:
            self._copy_dependency_libraries(project, target_dir, expander)
        
        # Copy dependfiles (assets, configs, etc.)
        if project.dependfiles:
            Reporter.info("Copying dependency files...")
            self._copy_depend_files(project, target_dir, expander)
        
        # Execute post-build commands
        if project.postbuildcommands:
            Reporter.info("Executing post-build commands...")
            if not self._execute_commands(project.postbuildcommands, expander):
                Display.error("Post-build commands failed")
                return False
        
        # Save cache
        if self.cache:
            for unit in units:
                self.cache.update(unit.source_file, unit.object_file, 
                                unit.include_dirs, unit.defines, unit.flags)
            self.cache.save()
        
        return True
    
    def _compile_units_parallel(self, units: List[CompilationUnit]) -> bool:
        """Compile units in parallel with real-time progress"""
        
        compiled_count = 0
        total_count = len(units)
        
        with ThreadPoolExecutor(max_workers=self.jobs) as executor:
            futures = {executor.submit(self._compile_unit, unit): unit for unit in units}
            
            for future in as_completed(futures):
                unit = futures[future]
                compiled_count += 1
                
                try:
                    success = future.result()
                    if success:
                        self.stats["compiled"] += 1
                        # Show real-time progress
                        source_name = Path(unit.source_file).name
                        progress = f"[{compiled_count}/{total_count}]"
                        Reporter.success(f"  {progress} Compiled: {source_name}")
                    else:
                        self.stats["failed"] += 1
                        Display.error(f"✗ Compilation failed: {unit.source_file}")
                        # Cancel remaining
                        for f in futures:
                            f.cancel()
                        return False
                except Exception as e:
                    Display.error(f"✗ Exception during compilation: {e}")
                    self.stats["failed"] += 1
                    return False
        
        return True
    
    def _compile_unit(self, unit: CompilationUnit) -> bool:
        """Compile a single compilation unit"""
        
        # Detect MSVC
        is_msvc = "cl.exe" in unit.compiler.lower() or "cl" == unit.compiler.lower()
        
        # Build command
        cmd = [unit.compiler]
        
        # Add flags
        cmd.extend(unit.flags)
        
        # Add defines
        for define in unit.defines:
            if is_msvc:
                cmd.append(f"/D{define}")
            else:
                cmd.append(f"-D{define}")
        
        # Add include directories
        for inc_dir in unit.include_dirs:
            if is_msvc:
                cmd.append(f"/I{inc_dir}")
            else:
                cmd.append(f"-I{inc_dir}")
        
        # Add source and output
        if is_msvc:
            cmd.extend(["/c", unit.source_file, f"/Fo{unit.object_file}"])
        else:
            cmd.extend(["-c", unit.source_file, "-o", unit.object_file])
        
        # Log command (only in verbose mode)
        if Reporter.verbose:
            Reporter.detail(f"  Command: {' '.join(cmd)}")
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.workspace.location
            )
            
            if result.returncode != 0:
                # Format error output beautifully
                source_name = Path(unit.source_file).name
                Display.error(f"\n╔{'═' * 78}╗")
                Display.error(f"║ Compilation Error: {source_name:<60} ║")
                Display.error(f"╠{'═' * 78}╣")
                
                # MSVC outputs to stdout, not stderr
                error_output = result.stderr if result.stderr else result.stdout
                
                if error_output:
                    # Parse and format compiler errors
                    for line in error_output.split('\n'):
                        if line.strip():
                            # Colorize error/warning keywords
                            if 'error' in line.lower():
                                line = line.replace('error', f'{Colors.RED}error{Colors.RESET}')
                                line = line.replace('Error', f'{Colors.RED}Error{Colors.RESET}')
                            elif 'warning' in line.lower():
                                line = line.replace('warning', f'{Colors.YELLOW}warning{Colors.RESET}')
                                line = line.replace('Warning', f'{Colors.YELLOW}Warning{Colors.RESET}')
                            Display.error(f"║ {line[:76]:<76} ║")
                
                Display.error(f"╚{'═' * 78}╝\n")
                return False
            
            return True
            
        except FileNotFoundError:
            Display.error(f"✗ Compiler not found: {unit.compiler}")
            return False
        except Exception as e:
            Display.error(f"✗ Compilation error: {e}")
            return False
    
    def _link(self, project: Project, toolchain, object_files: List[str],
             output_file: str, lib_dirs: List[str], links: List[str],
             expander: VariableExpander) -> bool:
        """Link object files into final executable/library"""
        
        Reporter.info("Linking...")
        
        linker = toolchain.linker or toolchain.compiler
        
        # Detect MSVC
        is_msvc = "cl.exe" in linker.lower() or "link.exe" in linker.lower() or "lib.exe" in linker.lower()
        
        # Build command based on project kind
        if project.kind == ProjectKind.STATIC_LIB:
            # Static library
            if is_msvc:
                archiver = "lib.exe"
                cmd = [archiver, "/nologo", f"/OUT:{output_file}"] + object_files
            else:
                archiver = toolchain.archiver or "ar"
                cmd = [archiver, "rcs", output_file] + object_files
        
        else:
            # Executable or shared library
            if is_msvc:
                # Use link.exe for MSVC
                cmd = ["link.exe", "/nologo"]
                
                # Add object files
                cmd.extend(object_files)
                
                # Output file
                cmd.append(f"/OUT:{output_file}")
                
                # Shared library specific
                if project.kind == ProjectKind.SHARED_LIB:
                    cmd.append("/DLL")
                
                # Debug info
                if project.symbols:
                    cmd.append("/DEBUG")
                
                # Add library directories
                for lib_dir in lib_dirs:
                    cmd.append(f"/LIBPATH:{lib_dir}")
                
                # Add libraries
                for link in links:
                    # Check if it's a dependency project
                    if link in self.workspace.projects:
                        dep_proj = self.workspace.projects[link]
                        dep_target_dir = Path(expander.expand(dep_proj.targetdir))
                        dep_name = dep_proj.targetname or dep_proj.name
                        
                        # Static library - use full path
                        if dep_proj.kind == ProjectKind.STATIC_LIB:
                            lib_file = dep_target_dir / f"{dep_name}.lib"
                            if lib_file.exists():
                                cmd.append(str(lib_file))
                            else:
                                Display.warning(f"Library not found: {lib_file}")
                        else:
                            # Shared library
                            cmd.append(f"{dep_name}.lib")
                    
                    # Full path to library file
                    elif link.endswith((".lib", ".dll")):
                        cmd.append(link)
                    
                    # System library
                    else:
                        # Add .lib extension for Windows system libraries
                        if not link.endswith(".lib"):
                            cmd.append(f"{link}.lib")
                        else:
                            cmd.append(link)
                
            else:
                # GCC/Clang
                cmd = [linker]
                
                # Add object files
                cmd.extend(object_files)
                
                # Add library directories
                for lib_dir in lib_dirs:
                    cmd.append(f"-L{lib_dir}")
                
                # Add libraries - with intelligent handling
                for link in links:
                    # Check if it's a dependency project
                    if link in self.workspace.projects:
                        dep_proj = self.workspace.projects[link]
                        dep_target_dir = Path(expander.expand(dep_proj.targetdir))
                        dep_name = dep_proj.targetname or dep_proj.name
                        
                        # Use full path to the library file
                        if dep_proj.kind == ProjectKind.STATIC_LIB:
                            # Static library - use full path
                            lib_file = dep_target_dir / f"{dep_name}.lib"
                            if not lib_file.exists():
                                lib_file = dep_target_dir / f"lib{dep_name}.a"
                            if lib_file.exists():
                                cmd.append(str(lib_file))
                            else:
                                Display.warning(f"Library not found: {lib_file}")
                        else:
                            # Shared library - use -l flag
                            cmd.append(f"-l{dep_name}")
                    
                    # Full path to library file
                    elif link.endswith((".a", ".lib", ".so", ".dll", ".dylib")):
                        cmd.append(link)
                    
                    # System library - check if valid for current platform
                    else:
                        # Filter platform-specific system libraries
                        if self._is_valid_system_library(link):
                            cmd.append(f"-l{link}")
                
                # Output file
                cmd.extend(["-o", output_file])
                
                # Shared library specific
                if project.kind == ProjectKind.SHARED_LIB:
                    cmd.append("-shared")
        
        # Log command
        if Reporter.verbose:
            Reporter.detail(f"  Link command: {' '.join(cmd)}")
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.workspace.location
            )
            
            if result.returncode != 0:
                Display.error("Linking failed")
                # MSVC outputs to stdout
                error_output = result.stderr if result.stderr else result.stdout
                if error_output:
                    print(error_output)
                return False
            
            self.stats["linked"] += 1
            return True
            
        except FileNotFoundError:
            Display.error(f"Linker not found: {linker}")
            return False
        except Exception as e:
            Display.error(f"Linking error: {e}")
            return False
    
    def _is_valid_system_library(self, lib_name: str) -> bool:
        """Check if a system library is valid for the current platform"""
        
        # Windows-specific libraries
        windows_libs = {"kernel32", "user32", "gdi32", "shell32", "advapi32", 
                       "ole32", "oleaut32", "uuid", "comdlg32", "winmm"}
        
        # Linux-specific libraries  
        linux_libs = {"pthread", "dl", "m", "rt", "X11", "GL", "GLU"}
        
        # macOS-specific libraries
        macos_libs = {"pthread", "dl", "m"}
        
        # Cross-platform libraries (available everywhere)
        common_libs = {"c", "stdc++", "gcc"}
        
        if lib_name in common_libs:
            return True
        
        if self.platform == "Windows" and lib_name in windows_libs:
            return True
        elif self.platform == "Linux" and lib_name in linux_libs:
            return True
        elif self.platform == "MacOS" and lib_name in macos_libs:
            return True
        else:
            # Unknown library - warn but allow (might be user-installed)
            if lib_name not in windows_libs | linux_libs | macos_libs:
                return True  # Allow unknown libraries
            else:
                Display.warning(f"Library '{lib_name}' not available on {self.platform}")
                return False
    
    def _resolve_source_files(self, project: Project, expander: VariableExpander) -> List[str]:
        """Resolve source files with wildcard expansion - ONLY source files, not headers"""
        
        base_dir = project.location or self.workspace.location
        
        # Resolve include patterns
        all_files = resolve_file_list(project.files, base_dir, expander)
        
        # Filter to keep only source files (not headers)
        source_extensions = {'.c', '.cpp', '.cc', '.cxx', '.m', '.mm'}
        source_files = [f for f in all_files if Path(f).suffix.lower() in source_extensions]
        
        # Resolve exclude patterns
        if project.excludefiles:
            exclude_files = set(resolve_file_list(project.excludefiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_files]
        
        # Exclude main files for tests
        if project.is_test and project.excludemainfiles:
            exclude_mains = set(resolve_file_list(project.excludemainfiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_mains]
        
        return source_files
    
    def _resolve_dependencies(self, project: Project, expander: VariableExpander) -> Tuple[List, List, List]:
        """Resolve project dependencies and collect include/lib directories"""
        
        all_includes = list(project.includedirs)
        all_libdirs = list(project.libdirs)
        all_links = list(project.links)
        
        # Add system-specific links
        if self.platform in project.system_links:
            all_links.extend(project.system_links[self.platform])
        
        # Process dependencies
        for dep_name in project.dependson:
            if dep_name not in self.workspace.projects:
                Display.warning(f"Dependency not found: {dep_name}")
                continue
            
            dep_project = self.workspace.projects[dep_name]
            
            # Add dependency's include directories
            all_includes.extend(dep_project.includedirs)
            
            # Add dependency's target directory as lib directory
            if dep_project.targetdir:
                dep_target_dir = expander.expand(dep_project.targetdir)
                all_libdirs.append(dep_target_dir)
            
            # Add dependency as library to link
            dep_target_name = dep_project.targetname or dep_project.name
            all_links.append(dep_target_name)
        
        # Expand variables in paths
        all_includes = [expander.expand(inc) for inc in all_includes]
        all_libdirs = [expander.expand(lib) for lib in all_libdirs]
        all_links = [expander.expand(link) for link in all_links]
        
        return all_includes, all_libdirs, all_links
    
    def _get_defines(self, project: Project, toolchain, expander: VariableExpander) -> List[str]:
        """Get all preprocessor defines"""
        
        defines = []
        
        # Toolchain defines
        defines.extend(toolchain.defines)
        
        # Project defines
        defines.extend(project.defines)
        
        # Configuration-specific defines
        for filter_expr, filter_defines in project._filtered_defines.items():
            if self._filter_matches(filter_expr):
                defines.extend(filter_defines)
        
        # Expand variables
        defines = [expander.expand(d) for d in defines]
        
        return defines
    
    def _get_compiler_flags(self, project: Project, toolchain, expander: VariableExpander) -> List[str]:
        """Get compiler flags"""
        
        flags = []
        
        # Detect if using MSVC
        compiler = self._get_compiler(toolchain, project.language.value == "C++")
        is_msvc = "cl.exe" in compiler.lower() or "cl" == compiler.lower()
        
        # C++ standard
        if project.language.value == "C++":
            if is_msvc:
                # MSVC syntax
                if "20" in project.cppdialect:
                    flags.append("/std:c++20")
                elif "17" in project.cppdialect:
                    flags.append("/std:c++17")
                elif "14" in project.cppdialect:
                    flags.append("/std:c++14")
                elif "11" in project.cppdialect:
                    flags.append("/std:c++11")
            else:
                # GCC/Clang syntax
                if "20" in project.cppdialect:
                    flags.append("-std=c++20")
                elif "17" in project.cppdialect:
                    flags.append("-std=c++17")
                elif "14" in project.cppdialect:
                    flags.append("-std=c++14")
                elif "11" in project.cppdialect:
                    flags.append("-std=c++11")
        
        # Optimization
        optimize_level = project.optimize
        for filter_expr, opt in project._filtered_optimize.items():
            if self._filter_matches(filter_expr):
                optimize_level = opt
        
        if is_msvc:
            # MSVC optimization flags
            if optimize_level == Optimization.OFF:
                flags.append("/Od")  # Disable optimization
            elif optimize_level == Optimization.SIZE:
                flags.append("/O1")  # Minimize size
            elif optimize_level == Optimization.SPEED:
                flags.append("/O2")  # Maximize speed
            elif optimize_level == Optimization.FULL:
                flags.append("/Ox")  # Full optimization
        else:
            # GCC/Clang optimization flags
            if optimize_level == Optimization.OFF:
                flags.append("-O0")
            elif optimize_level == Optimization.SIZE:
                flags.append("-Os")
            elif optimize_level == Optimization.SPEED:
                flags.append("-O2")
            elif optimize_level == Optimization.FULL:
                flags.append("-O3")
        
        # Debug symbols
        symbols = project.symbols
        for filter_expr, sym in project._filtered_symbols.items():
            if self._filter_matches(filter_expr):
                symbols = sym
        
        if symbols:
            if is_msvc:
                flags.extend(["/Zi", "/FS"])  # Debug info + file sharing
            else:
                flags.append("-g")
        
        # Position independent code for shared libraries
        if project.kind == ProjectKind.SHARED_LIB:
            if not is_msvc:  # MSVC handles this automatically
                flags.append("-fPIC")
        
        # MSVC-specific flags
        if is_msvc:
            flags.extend([
                "/EHsc",     # Exception handling
                "/W3",       # Warning level
                "/nologo",   # Suppress startup banner
            ])
            
            # Link with correct runtime library
            if self.config == "Debug":
                flags.append("/MDd")  # Multithreaded Debug DLL
            else:
                flags.append("/MD")   # Multithreaded DLL
        
        return flags
    
    def _filter_matches(self, filter_expr: str) -> bool:
        """Check if a filter expression matches current build configuration"""
        
        # Parse filter expression (e.g., "configurations:Debug", "system:Windows")
        if ":" not in filter_expr:
            return False
        
        filter_type, filter_value = filter_expr.split(":", 1)
        
        if filter_type == "configurations":
            return filter_value == self.config
        elif filter_type == "system":
            return filter_value == self.platform
        
        return False
    
    def _get_output_path(self, project: Project, target_dir: Path, 
                        expander: VariableExpander) -> str:
        """Get output file path"""
        
        target_name = project.targetname or project.name
        target_name = expander.expand(target_name)
        
        # Add appropriate extension
        if project.kind == ProjectKind.STATIC_LIB:
            if self.platform == "Windows":
                ext = ".lib"
            else:
                ext = ".a"
                target_name = f"lib{target_name}" if not target_name.startswith("lib") else target_name
        
        elif project.kind == ProjectKind.SHARED_LIB:
            if self.platform == "Windows":
                ext = ".dll"
            elif self.platform == "MacOS":
                ext = ".dylib"
            else:
                ext = ".so"
                target_name = f"lib{target_name}" if not target_name.startswith("lib") else target_name
        
        else:  # Executables
            if self.platform == "Windows":
                ext = ".exe"
            else:
                ext = ""
        
        return str(target_dir / f"{target_name}{ext}")
    
    def print_stats(self):
        """Print compilation statistics"""
        Reporter.section("Build Statistics")
        Reporter.info(f"  Compiled: {self.stats['compiled']} files")
        Reporter.info(f"  Cached:   {self.stats['cached']} files")
        Reporter.info(f"  Linked:   {self.stats['linked']} targets")
        if self.stats['failed'] > 0:
            Reporter.info(f"  Failed:   {self.stats['failed']} files")
    
    def _execute_commands(self, commands: List[str], expander: VariableExpander) -> bool:
        """Execute a list of commands"""
        for cmd_template in commands:
            # Expand variables in command
            cmd = expander.expand(cmd_template)
            
            Reporter.detail(f"  > {cmd}")
            
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.workspace.location
                )
                
                if result.returncode != 0:
                    Display.error(f"Command failed: {cmd}")
                    if result.stderr:
                        print(result.stderr)
                    return False
                
                # Print stdout if any
                if result.stdout and Reporter.verbose:
                    print(result.stdout)
                    
            except Exception as e:
                Display.error(f"Command execution error: {e}")
                return False
        
        return True
    
    def _get_compiler(self, toolchain, is_cpp: bool) -> str:
        """Get the appropriate compiler from toolchain"""
        if is_cpp:
            # C++ compiler
            if toolchain.cppcompiler_path:
                return toolchain.cppcompiler_path
            elif toolchain.cppcompiler:
                return toolchain.cppcompiler
            elif toolchain.compiler_path:
                return toolchain.compiler_path
            else:
                return toolchain.compiler
        else:
            # C compiler
            if toolchain.ccompiler_path:
                return toolchain.ccompiler_path
            elif toolchain.ccompiler:
                return toolchain.ccompiler
            elif toolchain.compiler_path:
                return toolchain.compiler_path
            else:
                return toolchain.compiler
    
    def _copy_dependency_libraries(self, project: Project, target_dir: Path, expander: VariableExpander):
        """
        Automatically copy shared libraries (.dll, .so, .dylib) from dependencies
        to the executable's directory
        """
        import shutil
        
        for dep_name in project.dependson:
            if dep_name not in self.workspace.projects:
                continue
            
            dep_project = self.workspace.projects[dep_name]
            
            # Only copy shared libraries
            if dep_project.kind != ProjectKind.SHARED_LIB:
                continue
            
            # Get dependency's target directory
            dep_target_dir = Path(expander.expand(dep_project.targetdir))
            
            # Determine library extension based on platform
            if self.platform == "Windows":
                lib_ext = ".dll"
            elif self.platform == "MacOS":
                lib_ext = ".dylib"
            else:  # Linux and others
                lib_ext = ".so"
            
            # Find the library file
            lib_name = dep_project.targetname or dep_project.name
            lib_file = dep_target_dir / f"{lib_name}{lib_ext}"
            
            # Alternative naming (lib prefix on Unix)
            if not lib_file.exists() and self.platform != "Windows":
                lib_file = dep_target_dir / f"lib{lib_name}{lib_ext}"
            
            if lib_file.exists():
                dest_file = target_dir / lib_file.name
                
                # Vérifier si le fichier existe déjà
                if dest_file.exists():
                    # Comparer la date de modification
                    if lib_file.stat().st_mtime <= dest_file.stat().st_mtime:
                        Reporter.detail(f"  Already exists (same or newer): {lib_file.name}")
                        continue
                
                try:
                    shutil.copy2(lib_file, dest_file)
                    Reporter.detail(f"  Copied: {lib_file.name}")
                except Exception as e:
                    Display.warning(f"Failed to copy {lib_file.name}: {e}")
    
    def _copy_depend_files(self, project: Project, target_dir: Path, expander: VariableExpander):
        """
        Copy dependency files (assets, configs, etc.) to target directory
        Supports wildcards: assets/**, config/*.json, etc.
        """
        import shutil
        from .variables import resolve_file_list, expand_path_patterns
        
        base_dir = project.location or self.workspace.location
        
        for pattern in project.dependfiles:
            # Expand variables
            expanded_pattern = expander.expand(pattern)
            
            # Check if pattern is a directory
            pattern_path = Path(expanded_pattern)
            if pattern_path.is_absolute():
                src_path = pattern_path
            else:
                src_path = Path(base_dir) / expanded_pattern
            
            # Handle directory patterns (e.g., "assets/**")
            if "**" in expanded_pattern or "*" in expanded_pattern:
                # Use wildcard expansion
                results = expand_path_patterns(expanded_pattern, base_dir)
                
                for file_path, is_exclude in results:
                    if is_exclude:
                        continue
                    
                    src_file = Path(file_path)
                    if not src_file.exists():
                        continue
                    
                    # Determine relative path to preserve directory structure
                    try:
                        if src_file.is_absolute():
                            # Try to get relative path from base_dir
                            rel_path = src_file.relative_to(base_dir)
                        else:
                            rel_path = src_file
                    except ValueError:
                        # Can't get relative path, use just filename
                        rel_path = src_file.name
                    
                    dest_file = target_dir / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(src_file, dest_file)
                        Reporter.detail(f"  Copied: {rel_path}")
                    except Exception as e:
                        Display.warning(f"Failed to copy {src_file}: {e}")
            
            # Handle single file or directory
            elif src_path.exists():
                if src_path.is_dir():
                    # Copy entire directory
                    dest_dir = target_dir / src_path.name
                    try:
                        if dest_dir.exists():
                            shutil.rmtree(dest_dir)
                        shutil.copytree(src_path, dest_dir)
                        Reporter.detail(f"  Copied directory: {src_path.name}")
                    except Exception as e:
                        Display.warning(f"Failed to copy directory {src_path}: {e}")
                else:
                    # Copy single file
                    dest_file = target_dir / src_path.name
                    try:
                        shutil.copy2(src_path, dest_file)
                        Reporter.detail(f"  Copied: {src_path.name}")
                    except Exception as e:
                        Display.warning(f"Failed to copy {src_path}: {e}")
            else:
                Display.warning(f"Depend file not found: {expanded_pattern}")

    def _get_main_file_for_platform(project, platform):
        """Retourne le fichier main approprié selon la plateforme"""
        
        if platform == "Android":
            # Android NDK utilise android_main
            return "Platform/Android/AndroidMain.cpp"
        
        elif platform == "Emscripten":
            # Emscripten utilise main classique mais avec SetMainLoop
            return "Platform/Emscripten/EmscriptenMain.cpp"
        
        elif platform in ["iOS"]:
            # iOS utilise UIApplicationMain
            return "Platform/iOS/iOSMain.mm"
        
        else:
            # Desktop: main.cpp standard
            return "Main.cpp"