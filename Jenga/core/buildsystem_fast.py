#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Ultra Fast Build System
Parallel compilation with ThreadPoolExecutor (compatible avec pickle)
"""

import os
import sys
import hashlib
import json
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
import queue
from enum import Enum
import pickle
import copy

try:
    from .api import Project, ProjectKind, Workspace, Optimization
    from .variables import VariableExpander, resolve_file_list, expand_path_patterns
except ImportError:
    from core.api import Project, ProjectKind, Workspace, Optimization
    from core.variables import VariableExpander, resolve_file_list, expand_path_patterns

try:
    from ..utils.display import Display, Colors
    from ..utils.reporter import Reporter
except ImportError:
    from utils.display import Display, Colors
    from utils.reporter import Reporter


class BuildMode(Enum):
    """Mode de build pour optimisation"""
    NORMAL = "normal"
    PARALLEL = "parallel"
    ULTRA = "ultra"  # Compilation + linkage parallèles


@dataclass
class CompilationJob:
    """Job de compilation (sérialisable pour pickle)"""
    job_id: int
    source_file: str
    object_file: str
    compiler: str
    command: List[str]
    workspace_dir: str  # Ajouté pour éviter les références globales
    defines: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    is_cpp: bool = True


@dataclass 
class LinkingJob:
    """Job de linkage (sérialisable)"""
    job_id: int
    project_name: str
    object_files: List[str]
    output_file: str
    linker: str
    command: List[str]
    workspace_dir: str  # Ajouté pour éviter les références globales
    lib_dirs: List[str] = field(default_factory=list)
    libraries: List[str] = field(default_factory=list)


def execute_compilation_job(job: CompilationJob) -> Tuple[int, bool, Optional[str]]:
    """Fonction autonome pour exécuter un job de compilation"""
    try:
        start_time = time.time()
        
        result = subprocess.run(
            job.command,
            capture_output=True,
            text=True,
            cwd=job.workspace_dir,
            timeout=300
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            return (job.job_id, True, f"{Path(job.source_file).name} ({elapsed:.2f}s)")
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return (job.job_id, False, error_msg[:500])
            
    except subprocess.TimeoutExpired:
        return (job.job_id, False, "Timeout (5 minutes)")
    except Exception as e:
        return (job.job_id, False, str(e))


def execute_linking_job(job: LinkingJob) -> Tuple[int, bool, Optional[str]]:
    """Fonction autonome pour exécuter un job de linkage"""
    try:
        start_time = time.time()
        
        result = subprocess.run(
            job.command,
            capture_output=True,
            text=True,
            cwd=job.workspace_dir,
            timeout=600
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            return (job.job_id, True, f"{job.project_name} ({elapsed:.2f}s)")
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return (job.job_id, False, error_msg[:500])
            
    except subprocess.TimeoutExpired:
        return (job.job_id, False, "Timeout (10 minutes)")
    except Exception as e:
        return (job.job_id, False, str(e))


class FastBuildCache:
    """Cache de build ultra-rapide avec stockage binaire"""
    
    def __init__(self, workspace_location: str):
        self.cache_dir = Path(workspace_location) / ".jenga_cache"
        self.cache_file = self.cache_dir / "build_cache.bin"
        self.dep_cache_file = self.cache_dir / "deps_cache.bin"
        self.cache_data: Dict[str, Dict] = {}
        self.deps_cache: Dict[str, List[str]] = {}
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.load()
    
    def load(self):
        """Charge le cache depuis le disque (format binaire)"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    self.cache_data = pickle.load(f)
            
            if self.dep_cache_file.exists():
                with open(self.dep_cache_file, 'rb') as f:
                    self.deps_cache = pickle.load(f)
                    
        except Exception as e:
            self.cache_data = {}
            self.deps_cache = {}
    
    def save(self):
        """Sauvegarde le cache sur le disque (format binaire)"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            with open(self.dep_cache_file, 'wb') as f:
                pickle.dump(self.deps_cache, f, protocol=pickle.HIGHEST_PROTOCOL)
                
        except Exception as e:
            pass
    
    def get_file_signature(self, file_path: str) -> str:
        """Signature ultra-rapide d'un fichier (mtime + size)"""
        try:
            stat = os.stat(file_path)
            return f"{stat.st_mtime}:{stat.st_size}"
        except:
            return ""
    
    def needs_rebuild(self, source_file: str, object_file: str, 
                     defines: List[str], flags: List[str]) -> bool:
        """Vérifie si un fichier doit être recompilé (ultra-rapide)"""
        
        # 1. Fichier objet n'existe pas
        if not Path(object_file).exists():
            return True
        
        # 2. Pas dans le cache
        if source_file not in self.cache_data:
            return True
        
        cached = self.cache_data[source_file]
        
        # 3. Signature source différente
        current_sig = self.get_file_signature(source_file)
        if cached.get("source_sig") != current_sig:
            return True
        
        # 4. Options de compilation différentes
        current_opts = {
            "defines": tuple(sorted(defines)),  # Tuple pour être hashable
            "flags": tuple(sorted(flags)),
            "object_file": object_file
        }
        
        if cached.get("options") != current_opts:
            return True
        
        return False
    
    def update(self, source_file: str, object_file: str, 
               defines: List[str], flags: List[str]):
        """Met à jour une entrée du cache"""
        self.cache_data[source_file] = {
            "source_sig": self.get_file_signature(source_file),
            "options": {
                "defines": tuple(sorted(defines)),
                "flags": tuple(sorted(flags)),
                "object_file": object_file
            },
            "timestamp": time.time()
        }


class UltraFastCompiler:
    """Compilateur ultra-rapide avec parallélisation complète"""
    
    def __init__(self, workspace: Workspace, config: str, platform: str, 
                 jobs: int = None, use_cache: bool = True, mode: BuildMode = BuildMode.ULTRA):
        self.workspace = workspace
        self.config = config
        self.platform = platform
        self.jobs = jobs or max(1, multiprocessing.cpu_count())
        self.use_cache = use_cache
        self.mode = mode
        
        # Cache
        self.cache = FastBuildCache(workspace.location) if use_cache else None
        
        # Statistiques
        self.stats = {
            "compiled": 0,
            "cached": 0,
            "failed": 0,
            "linked": 0,
            "total_time": 0.0,
            "compilation_time": 0.0,
            "linking_time": 0.0
        }
        
        # Synchronisation
        self.lock = threading.Lock()
        
        Display.info(f"⚡ Build mode: {mode.value}")
        Display.info(f"🧵 Parallel jobs: {self.jobs}")
    
    def compile_project(self, project: Project, toolchain_name: str = "default") -> bool:
        """Compile un projet avec parallélisation maximale"""
        
        total_start = time.time()
        
        Reporter.section(f"Building project: {project.name}")
        
        # Récupérer le toolchain
        if project.toolchain:
            toolchain_name = project.toolchain
        
        if toolchain_name not in self.workspace.toolchains:
            Display.error(f"Toolchain '{toolchain_name}' not found")
            return False
        
        toolchain = self.workspace.toolchains[toolchain_name]
        
        # Expander de variables
        expander = VariableExpander(self.workspace, project, self.config, self.platform)
        
        # Exécuter les commandes pré-build (séquentiel)
        if project.prebuildcommands:
            if not self._execute_commands_sequential(project.prebuildcommands, expander):
                return False
        
        # Résoudre les dépendances
        includes, lib_dirs, links = self._resolve_dependencies_fast(project, expander)
        
        # Résoudre les fichiers sources
        source_files = self._resolve_source_files_fast(project, expander)
        
        if not source_files:
            Display.warning(f"No source files found for project {project.name}")
            return True
        
        Reporter.info(f"📁 Found {len(source_files)} source file(s)")
        
        # Créer les répertoires
        obj_dir = Path(expander.expand(project.objdir))
        target_dir = Path(expander.expand(project.targetdir))
        
        obj_dir.mkdir(parents=True, exist_ok=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Récupérer les paramètres
        defines = self._get_defines_fast(project, toolchain, expander)
        flags = self._get_compiler_flags_fast(project, toolchain, expander)
        
        # Créer les jobs de compilation
        compilation_jobs = []
        cached_count = 0
        
        for i, src_file in enumerate(source_files):
            src_path = Path(src_file)
            obj_file = str(obj_dir / src_path.with_suffix(".o").name)
            
            is_cpp = src_path.suffix in ['.cpp', '.cc', '.cxx', '.hpp', '.inl']
            compiler = self._get_compiler_fast(toolchain, is_cpp)
            
            # Vérifier le cache
            if self.cache and not self.cache.needs_rebuild(src_file, obj_file, defines, flags):
                with self.lock:
                    self.stats["cached"] += 1
                    cached_count += 1
                continue
            
            # Construire la commande
            cmd = self._build_compile_command(compiler, src_file, obj_file, 
                                            includes, defines, flags)
            
            job = CompilationJob(
                job_id=i,
                source_file=src_file,
                object_file=obj_file,
                compiler=compiler,
                command=cmd,
                workspace_dir=self.workspace.location,
                defines=defines,
                includes=includes,
                flags=flags,
                is_cpp=is_cpp
            )
            
            compilation_jobs.append(job)
        
        # Afficher les statistiques de cache
        if cached_count > 0:
            Reporter.success(f"💾 {cached_count} file(s) up to date (cached)")
        
        # Exécuter la compilation en parallèle
        if compilation_jobs:
            compile_start = time.time()
            
            success = self._execute_compilation_parallel(compilation_jobs)
            
            compile_time = time.time() - compile_start
            self.stats["compilation_time"] += compile_time
            
            if not success:
                return False
            
            # Mettre à jour le cache
            if self.cache:
                for job in compilation_jobs:
                    if Path(job.object_file).exists():
                        self.cache.update(job.source_file, job.object_file, 
                                        job.defines, job.flags)
        
        # Prépare-link (séquentiel)
        if project.prelinkcommands:
            if not self._execute_commands_sequential(project.prelinkcommands, expander):
                return False
        
        # Linkage
        object_files = [str(obj_dir / Path(src).with_suffix(".o").name) for src in source_files]
        output_file = self._get_output_path_fast(project, target_dir, expander)
        
        link_start = time.time()
        
        success = self._execute_linking(project, toolchain, object_files, 
                                      output_file, lib_dirs, links, expander)
        
        link_time = time.time() - link_start
        self.stats["linking_time"] += link_time
        
        if not success:
            return False
        
        # Post-link (séquentiel)
        if project.postlinkcommands:
            if not self._execute_commands_sequential(project.postlinkcommands, expander):
                return False
        
        # Copier les dépendances
        if project.kind in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP]:
            self._copy_dependency_libraries_fast(project, target_dir, expander)
        
        # Copier les fichiers dépendants
        if project.dependfiles:
            self._copy_depend_files_fast(project, target_dir, expander)
        
        # Post-build (séquentiel)
        if project.postbuildcommands:
            if not self._execute_commands_sequential(project.postbuildcommands, expander):
                return False
        
        # Sauvegarder le cache
        if self.cache:
            self.cache.save()
        
        # Statistiques
        total_time = time.time() - total_start
        self.stats["total_time"] += total_time
        
        Reporter.success(f"✅ Built: {output_file} ({total_time:.2f}s)")
        
        return True
    
    def _execute_compilation_parallel(self, jobs: List[CompilationJob]) -> bool:
        """Exécute la compilation en parallèle avec ThreadPoolExecutor"""
        
        if not jobs:
            return True
        
        total_jobs = len(jobs)
        Reporter.info(f"🔨 Compiling {total_jobs} file(s) in parallel...")
        
        # Utiliser ThreadPoolExecutor (compatible avec pickle)
        with ThreadPoolExecutor(max_workers=self.jobs) as executor:
            # Soumettre tous les jobs
            future_to_job = {}
            for job in jobs:
                future = executor.submit(execute_compilation_job, job)
                future_to_job[future] = job
            
            completed = 0
            failed_jobs = []
            
            # Afficher la progression
            progress_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            progress_idx = 0
            
            # Traiter les résultats au fur et à mesure
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                
                try:
                    job_id, success, message = future.result(timeout=310)
                    
                    if success:
                        with self.lock:
                            self.stats["compiled"] += 1
                            completed += 1
                        
                        # Afficher le succès avec une jolie progression
                        progress = progress_chars[progress_idx % len(progress_chars)]
                        print(f"\r  {progress} [{completed}/{total_jobs}] {message}", end="", flush=True)
                        progress_idx += 1
                    else:
                        with self.lock:
                            self.stats["failed"] += 1
                        
                        failed_jobs.append((job.source_file, message))
                        print(f"\r  ✗ {Path(job.source_file).name}: {message}")
                        
                except Exception as e:
                    failed_jobs.append((job.source_file, str(e)))
                    print(f"\r  ✗ {Path(job.source_file).name}: {e}")
        
        print()  # Nouvelle ligne à la fin
        
        # Afficher les erreurs
        if failed_jobs:
            Display.error("\n╔═══════════════════════════════════════════════════════════╗")
            Display.error("║                    COMPILATION FAILED                    ║")
            Display.error("╠═══════════════════════════════════════════════════════════╣")
            
            for source_file, error in failed_jobs:
                Display.error(f"║ {Path(source_file).name:<55} ║")
                if error:
                    Display.error(f"║   {error:<53} ║")
            
            Display.error("╚═══════════════════════════════════════════════════════════╝")
            return False
        
        return True
    
    def _execute_linking(self, project: Project, toolchain, object_files: List[str],
                        output_file: str, lib_dirs: List[str], links: List[str],
                        expander: VariableExpander) -> bool:
        """Exécute le linkage"""
        
        Reporter.info("🔗 Linking...")
        
        linker = toolchain.linker or toolchain.compiler
        
        # Construire la commande de linkage
        cmd = self._build_link_command(project, toolchain, object_files, output_file, 
                                      lib_dirs, links, expander)
        
        if not cmd:
            return False
        
        # Créer le job de linkage
        job = LinkingJob(
            job_id=0,
            project_name=project.name,
            object_files=object_files,
            output_file=output_file,
            linker=linker,
            command=cmd,
            workspace_dir=self.workspace.location,
            lib_dirs=lib_dirs,
            libraries=links
        )
        
        # Exécuter le linkage
        job_id, success, message = execute_linking_job(job)
        
        if success:
            with self.lock:
                self.stats["linked"] += 1
            Reporter.success(f"  ✓ {message}")
            return True
        else:
            Display.error(f"✗ Linking failed: {message}")
            return False
    
    def _build_compile_command(self, compiler: str, source_file: str, object_file: str,
                              includes: List[str], defines: List[str], flags: List[str]) -> List[str]:
        """Construit la commande de compilation optimisée"""
        
        is_msvc = "cl.exe" in compiler.lower() or "cl" == compiler.lower()
        
        cmd = [compiler]
        cmd.extend(flags)
        
        # Définitions
        for define in defines:
            if is_msvc:
                cmd.append(f"/D{define}")
            else:
                cmd.append(f"-D{define}")
        
        # Répertoires d'inclusion
        for inc_dir in includes:
            if is_msvc:
                cmd.append(f"/I{inc_dir}")
            else:
                cmd.append(f"-I{inc_dir}")
        
        # Fichier source et sortie
        if is_msvc:
            cmd.extend(["/c", source_file, f"/Fo{object_file}"])
        else:
            cmd.extend(["-c", source_file, "-o", object_file])
        
        # Optimisations pour la vitesse de compilation
        if not is_msvc:
            cmd.append("-pipe")  # Utiliser des pipes pour la communication
        
        return cmd
    
    def _build_link_command(self, project: Project, toolchain, object_files: List[str],
                           output_file: str, lib_dirs: List[str], links: List[str],
                           expander: VariableExpander) -> Optional[List[str]]:
        """Construit la commande de linkage"""
        
        linker = toolchain.linker or toolchain.compiler
        is_msvc = "cl.exe" in linker.lower() or "link.exe" in linker.lower()
        
        if project.kind == ProjectKind.STATIC_LIB:
            # Bibliothèque statique
            if is_msvc:
                archiver = "lib.exe"
                return [archiver, "/nologo", f"/OUT:{output_file}"] + object_files
            else:
                archiver = toolchain.archiver or "ar"
                return [archiver, "rcs", output_file] + object_files
        
        else:
            # Exécutable ou bibliothèque partagée
            if is_msvc:
                cmd = ["link.exe", "/nologo"]
                cmd.extend(object_files)
                cmd.append(f"/OUT:{output_file}")
                
                if project.kind == ProjectKind.SHARED_LIB:
                    cmd.append("/DLL")
                
                if project.symbols:
                    cmd.append("/DEBUG")
                
                for lib_dir in lib_dirs:
                    cmd.append(f"/LIBPATH:{lib_dir}")
                
                for link in links:
                    if link in self.workspace.projects:
                        dep = self.workspace.projects[link]
                        dep_dir = Path(expander.expand(dep.targetdir))
                        dep_name = dep.targetname or dep.name
                        
                        if dep.kind == ProjectKind.STATIC_LIB:
                            lib_file = dep_dir / f"{dep_name}.lib"
                            if lib_file.exists():
                                cmd.append(str(lib_file))
                    elif link.endswith((".lib", ".dll")):
                        cmd.append(link)
                    else:
                        if not link.endswith(".lib"):
                            cmd.append(f"{link}.lib")
                        else:
                            cmd.append(link)
                
                return cmd
            else:
                cmd = [linker]
                cmd.extend(object_files)
                
                for lib_dir in lib_dirs:
                    cmd.append(f"-L{lib_dir}")
                
                for link in links:
                    if link in self.workspace.projects:
                        dep = self.workspace.projects[link]
                        dep_dir = Path(expander.expand(dep.targetdir))
                        dep_name = dep.targetname or dep.name
                        
                        if dep.kind == ProjectKind.STATIC_LIB:
                            lib_file = dep_dir / f"{dep_name}.lib"
                            if not lib_file.exists():
                                lib_file = dep_dir / f"lib{dep_name}.a"
                            if lib_file.exists():
                                cmd.append(str(lib_file))
                        else:
                            cmd.append(f"-l{dep_name}")
                    elif link.endswith((".a", ".lib", ".so", ".dll", ".dylib")):
                        cmd.append(link)
                    else:
                        cmd.append(f"-l{link}")
                
                cmd.extend(["-o", output_file])
                
                if project.kind == ProjectKind.SHARED_LIB:
                    cmd.append("-shared")
                
                return cmd
    
    def _resolve_source_files_fast(self, project: Project, expander: VariableExpander) -> List[str]:
        """Résolution rapide des fichiers sources"""
        
        base_dir = project.location or self.workspace.location
        
        # Résolution des patterns
        all_files = resolve_file_list(project.files, base_dir, expander)
        
        # Filtrer les fichiers source uniquement
        source_extensions = {'.c', '.cpp', '.cc', '.cxx', '.m', '.mm'}
        source_files = [f for f in all_files if Path(f).suffix.lower() in source_extensions]
        
        # Exclusions
        if project.excludefiles:
            exclude_files = set(resolve_file_list(project.excludefiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_files]
        
        # Exclusions de main pour les tests
        if project.is_test and project.excludemainfiles:
            exclude_mains = set(resolve_file_list(project.excludemainfiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_mains]
        
        return source_files
    
    def _resolve_dependencies_fast(self, project: Project, expander: VariableExpander) -> Tuple[List, List, List]:
        """Résolution rapide des dépendances"""
        
        includes = list(project.includedirs)
        lib_dirs = list(project.libdirs)
        links = list(project.links)
        
        # Liens spécifiques à la plateforme
        if self.platform in project.system_links:
            links.extend(project.system_links[self.platform])
        
        # Dépendances du projet
        for dep_name in project.dependson:
            if dep_name in self.workspace.projects:
                dep = self.workspace.projects[dep_name]
                includes.extend(dep.includedirs)
                
                if dep.targetdir:
                    lib_dirs.append(expander.expand(dep.targetdir))
                
                links.append(dep.targetname or dep.name)
        
        # Expansion des variables
        includes = [expander.expand(inc) for inc in includes]
        lib_dirs = [expander.expand(lib) for lib in lib_dirs]
        links = [expander.expand(link) for link in links]
        
        return includes, lib_dirs, links
    
    def _get_defines_fast(self, project: Project, toolchain, expander: VariableExpander) -> List[str]:
        """Récupération rapide des définitions"""
        
        defines = []
        defines.extend(toolchain.defines)
        defines.extend(project.defines)
        
        # Définitions filtrées
        for filter_expr, filter_defines in project._filtered_defines.items():
            if self._filter_matches(filter_expr):
                defines.extend(filter_defines)
        
        return [expander.expand(d) for d in defines]
    
    def _get_compiler_flags_fast(self, project: Project, toolchain, expander: VariableExpander) -> List[str]:
        """Récupération rapide des flags"""
        
        flags = []
        
        # Détecter MSVC
        compiler = self._get_compiler_fast(toolchain, project.language.value == "C++")
        is_msvc = "cl.exe" in compiler.lower() or "cl" == compiler.lower()
        
        # Standard C++
        if project.language.value == "C++":
            if is_msvc:
                if "20" in project.cppdialect: flags.append("/std:c++20")
                elif "17" in project.cppdialect: flags.append("/std:c++17")
                elif "14" in project.cppdialect: flags.append("/std:c++14")
                elif "11" in project.cppdialect: flags.append("/std:c++11")
            else:
                if "20" in project.cppdialect: flags.append("-std=c++20")
                elif "17" in project.cppdialect: flags.append("-std=c++17")
                elif "14" in project.cppdialect: flags.append("-std=c++14")
                elif "11" in project.cppdialect: flags.append("-std=c++11")
        
        # Optimisation
        optimize = project.optimize
        for filter_expr, opt in project._filtered_optimize.items():
            if self._filter_matches(filter_expr):
                optimize = opt
        
        if is_msvc:
            if optimize == Optimization.OFF: flags.append("/Od")
            elif optimize == Optimization.SIZE: flags.append("/O1")
            elif optimize == Optimization.SPEED: flags.append("/O2")
            elif optimize == Optimization.FULL: flags.append("/Ox")
        else:
            if optimize == Optimization.OFF: flags.append("-O0")
            elif optimize == Optimization.SIZE: flags.append("-Os")
            elif optimize == Optimization.SPEED: flags.append("-O2")
            elif optimize == Optimization.FULL: flags.append("-O3")
        
        # Symboles de debug
        symbols = project.symbols
        for filter_expr, sym in project._filtered_symbols.items():
            if self._filter_matches(filter_expr):
                symbols = sym
        
        if symbols:
            if is_msvc:
                flags.extend(["/Zi", "/FS"])
            else:
                flags.append("-g")
        
        # PIC pour les bibliothèques partagées
        if project.kind == ProjectKind.SHARED_LIB and not is_msvc:
            flags.append("-fPIC")
        
        # Flags MSVC
        if is_msvc:
            flags.extend(["/EHsc", "/W3", "/nologo"])
            if self.config == "Debug":
                flags.append("/MDd")
            else:
                flags.append("/MD")
        
        return flags
    
    def _filter_matches(self, filter_expr: str) -> bool:
        """Vérifie si un filtre correspond"""
        if ":" not in filter_expr:
            return False
        
        filter_type, filter_value = filter_expr.split(":", 1)
        
        if filter_type == "configurations":
            return filter_value == self.config
        elif filter_type == "system":
            return filter_value == self.platform
        
        return False
    
    def _get_output_path_fast(self, project: Project, target_dir: Path, 
                             expander: VariableExpander) -> str:
        """Chemin de sortie rapide"""
        
        target_name = project.targetname or project.name
        target_name = expander.expand(target_name)
        
        if project.kind == ProjectKind.STATIC_LIB:
            if self.platform == "Windows":
                ext = ".lib"
            else:
                ext = ".a"
                if not target_name.startswith("lib"):
                    target_name = f"lib{target_name}"
        
        elif project.kind == ProjectKind.SHARED_LIB:
            if self.platform == "Windows":
                ext = ".dll"
            elif self.platform == "MacOS":
                ext = ".dylib"
            else:
                ext = ".so"
                if not target_name.startswith("lib"):
                    target_name = f"lib{target_name}"
        
        else:
            if self.platform == "Windows":
                ext = ".exe"
            else:
                ext = ""
        
        return str(target_dir / f"{target_name}{ext}")
    
    def _get_compiler_fast(self, toolchain, is_cpp: bool) -> str:
        """Récupération rapide du compilateur"""
        if is_cpp:
            if toolchain.cppcompiler_path:
                return toolchain.cppcompiler_path
            elif toolchain.cppcompiler:
                return toolchain.cppcompiler
            elif toolchain.compiler_path:
                return toolchain.compiler_path
            else:
                return toolchain.compiler
        else:
            if toolchain.ccompiler_path:
                return toolchain.ccompiler_path
            elif toolchain.ccompiler:
                return toolchain.ccompiler
            elif toolchain.compiler_path:
                return toolchain.compiler_path
            else:
                return toolchain.compiler
    
    def _execute_commands_sequential(self, commands: List[str], expander: VariableExpander) -> bool:
        """Exécute des commandes séquentielles"""
        for cmd_template in commands:
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
                    
            except Exception as e:
                Display.error(f"Command execution error: {e}")
                return False
        
        return True
    
    def _copy_dependency_libraries_fast(self, project: Project, target_dir: Path, expander: VariableExpander):
        """Copie rapide des bibliothèques de dépendances"""
        import shutil
        
        for dep_name in project.dependson:
            if dep_name not in self.workspace.projects:
                continue
            
            dep = self.workspace.projects[dep_name]
            if dep.kind != ProjectKind.SHARED_LIB:
                continue
            
            dep_dir = Path(expander.expand(dep.targetdir))
            lib_name = dep.targetname or dep.name
            
            if self.platform == "Windows":
                lib_ext = ".dll"
            elif self.platform == "MacOS":
                lib_ext = ".dylib"
            else:
                lib_ext = ".so"
            
            lib_file = dep_dir / f"{lib_name}{lib_ext}"
            
            if not lib_file.exists() and self.platform != "Windows":
                lib_file = dep_dir / f"lib{lib_name}{lib_ext}"
            
            if lib_file.exists():
                dest_file = target_dir / lib_file.name
                
                if dest_file.exists():
                    if lib_file.stat().st_mtime <= dest_file.stat().st_mtime:
                        continue
                
                try:
                    shutil.copy2(lib_file, dest_file)
                except Exception as e:
                    pass
    
    def _copy_depend_files_fast(self, project: Project, target_dir: Path, expander: VariableExpander):
        """Copie rapide des fichiers dépendants"""
        import shutil
        
        base_dir = project.location or self.workspace.location
        
        for pattern in project.dependfiles:
            expanded = expander.expand(pattern)
            pattern_path = Path(expanded)
            
            if pattern_path.is_absolute():
                src_path = pattern_path
            else:
                src_path = Path(base_dir) / expanded
            
            if "**" in expanded or "*" in expanded:
                results = expand_path_patterns(expanded, base_dir)
                
                for file_path, is_exclude in results:
                    if is_exclude:
                        continue
                    
                    src_file = Path(file_path)
                    if not src_file.exists():
                        continue
                    
                    try:
                        if src_file.is_absolute():
                            rel_path = src_file.relative_to(base_dir)
                        else:
                            rel_path = src_file
                    except ValueError:
                        rel_path = src_file.name
                    
                    dest_file = target_dir / rel_path
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(src_file, dest_file)
                    except Exception as e:
                        pass
            
            elif src_path.exists():
                if src_path.is_dir():
                    dest_dir = target_dir / src_path.name
                    try:
                        if dest_dir.exists():
                            shutil.rmtree(dest_dir)
                        shutil.copytree(src_path, dest_dir)
                    except Exception as e:
                        pass
                else:
                    dest_file = target_dir / src_path.name
                    try:
                        shutil.copy2(src_path, dest_file)
                    except Exception as e:
                        pass
    
    def print_stats(self):
        """Affiche les statistiques détaillées"""
        Reporter.section("Build Statistics")
        Reporter.info(f"  Compiled:     {self.stats['compiled']} files")
        Reporter.info(f"  Cached:       {self.stats['cached']} files")
        Reporter.info(f"  Linked:       {self.stats['linked']} targets")
        
        if self.stats['failed'] > 0:
            Reporter.info(f"  Failed:       {self.stats['failed']} files")
        
        Reporter.info(f"  Total time:   {self.stats['total_time']:.2f}s")
        Reporter.info(f"  Compile time: {self.stats['compilation_time']:.2f}s")
        Reporter.info(f"  Link time:    {self.stats['linking_time']:.2f}s")
        
        # Calculer la vitesse
        if self.stats['compiled'] > 0 and self.stats['compilation_time'] > 0:
            speed = self.stats['compiled'] / self.stats['compilation_time']
            Reporter.info(f"  Compile speed: {speed:.1f} files/second")