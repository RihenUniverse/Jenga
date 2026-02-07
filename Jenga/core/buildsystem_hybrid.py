#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Hybrid Fast Build System
Combinaison ThreadPoolExecutor + ProcessPoolExecutor pour maximiser les performances
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
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
    ULTRA = "ultra"
    HYBRID = "hybrid"  # Threads + Processes


@dataclass
class SimpleCompilationJob:
    """Job de compilation simple (sérialisable pour multiprocessing)"""
    job_id: int
    command: List[str]
    source_file: str
    object_file: str
    workspace_dir: str


@dataclass 
class SimpleLinkingJob:
    """Job de linkage simple (sérialisable)"""
    job_id: int
    command: List[str]
    project_name: str
    output_file: str
    workspace_dir: str


def execute_simple_compilation_job(job: SimpleCompilationJob) -> Tuple[int, bool, Optional[str]]:
    """Fonction autonome pour exécuter un job de compilation (pour multiprocessing)"""
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
            # Limiter la taille du message d'erreur pour éviter les problèmes de sérialisation
            return (job.job_id, False, error_msg[:200])
            
    except subprocess.TimeoutExpired:
        return (job.job_id, False, "Timeout (5 minutes)")
    except Exception as e:
        return (job.job_id, False, str(e)[:200])


def execute_simple_linking_job(job: SimpleLinkingJob) -> Tuple[int, bool, Optional[str]]:
    """Fonction autonome pour exécuter un job de linkage (pour multiprocessing)"""
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
            return (job.job_id, False, error_msg[:200])
            
    except subprocess.TimeoutExpired:
        return (job.job_id, False, "Timeout (10 minutes)")
    except Exception as e:
        return (job.job_id, False, str(e)[:200])


class HybridBuildCache:
    """Cache de build hybride avec stockage binaire"""
    
    def __init__(self, workspace_location: str):
        self.cache_dir = Path(workspace_location) / ".jenga_cache"
        self.cache_file = self.cache_dir / "hybrid_cache.bin"
        self.cache_data: Dict[str, Dict] = {}
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.load()
    
    def load(self):
        """Charge le cache depuis le disque"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    self.cache_data = pickle.load(f)
        except:
            self.cache_data = {}
    
    def save(self):
        """Sauvegarde le cache sur le disque"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            pass
    
    def get_file_signature(self, file_path: str) -> str:
        """Signature ultra-rapide d'un fichier"""
        try:
            stat = os.stat(file_path)
            return f"{stat.st_mtime}:{stat.st_size}"
        except:
            return ""
    
    def needs_rebuild(self, source_file: str, object_file: str, 
                     defines: List[str], flags: List[str]) -> bool:
        """Vérifie si un fichier doit être recompilé"""
        
        # Fichier objet n'existe pas
        if not Path(object_file).exists():
            return True
        
        # Pas dans le cache
        if source_file not in self.cache_data:
            return True
        
        cached = self.cache_data[source_file]
        
        # Signature source différente
        current_sig = self.get_file_signature(source_file)
        if cached.get("source_sig") != current_sig:
            return True
        
        # Options de compilation différentes
        current_opts = {
            "defines": tuple(sorted(defines)),
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


class HybridCompiler:
    """Compilateur hybride avec parallélisation optimale"""
    
    def __init__(self, workspace: Workspace, config: str, platform: str, 
                 jobs: int = None, use_cache: bool = True, mode: BuildMode = BuildMode.HYBRID):
        self.workspace = workspace
        self.config = config
        self.platform = platform
        self.jobs = jobs or max(1, multiprocessing.cpu_count())
        self.use_cache = use_cache
        self.mode = mode
        
        # Déterminer le nombre de processus et threads
        self.cpu_count = multiprocessing.cpu_count()
        self.process_count = max(1, self.cpu_count // 2)  # 50% pour les processus
        self.thread_count = max(2, self.jobs - self.process_count)  # Le reste pour les threads
        
        # Cache
        self.cache = HybridBuildCache(workspace.location) if use_cache else None
        
        # Statistiques
        self.stats = {
            "compiled": 0,
            "cached": 0,
            "failed": 0,
            "linked": 0,
            "total_time": 0.0,
            "compilation_time": 0.0,
            "linking_time": 0.0,
            "process_compiled": 0,
            "thread_compiled": 0
        }
        
        # Synchronisation
        self.lock = threading.Lock()
        
        Display.info(f"⚡ Build mode: {mode.value}")
        Display.info(f"🖥️  CPU cores: {self.cpu_count}")
        Display.info(f"🧵 Threads: {self.thread_count}, Processes: {self.process_count}")
    
    def compile_project(self, project: Project, toolchain_name: str = "default") -> bool:
        """Compile un projet avec stratégie hybride"""
        
        # Vérifier si c'est un projet caché (comme __Unitest__)
        is_hidden_project = project.name.startswith("__")
        
        total_start = time.time()
        
        if is_hidden_project:
            Reporter.section(f"Building hidden project: {project.name}")
        else:
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
        
        # Exécuter les commandes pré-build
        if project.prebuildcommands:
            if not self._execute_commands_sequential(project.prebuildcommands, expander):
                return False
        
        # Résoudre les dépendances (INCLURE les projets cachés comme __Unitest__)
        includes, lib_dirs, links = self._resolve_dependencies_hybrid(project, expander)
        
        # Résoudre les fichiers sources
        source_files = self._resolve_source_files_hybrid(project, expander)
        
        if not source_files:
            if not is_hidden_project:  # Ne pas afficher l'avertissement pour les projets cachés
                Display.warning(f"No source files found for project {project.name}")
            return True
        
        if is_hidden_project:
            Reporter.info(f"🔧 Found {len(source_files)} source file(s) for hidden project")
        else:
            Reporter.info(f"📁 Found {len(source_files)} source file(s)")
        
        # Créer les répertoires
        obj_dir = Path(expander.expand(project.objdir))
        target_dir = Path(expander.expand(project.targetdir))
        
        obj_dir.mkdir(parents=True, exist_ok=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Récupérer les paramètres
        defines = self._get_defines_hybrid(project, toolchain, expander)
        flags = self._get_compiler_flags_hybrid(project, toolchain, expander)
        
        # Créer les jobs de compilation
        compilation_jobs = []
        cached_count = 0
        
        for i, src_file in enumerate(source_files):
            src_path = Path(src_file)
            obj_file = str(obj_dir / src_path.with_suffix(".o").name)
            
            is_cpp = src_path.suffix in ['.cpp', '.cc', '.cxx', '.hpp', '.inl']
            compiler = self._get_compiler_hybrid(toolchain, is_cpp)
            
            # Vérifier le cache
            if self.cache and not self.cache.needs_rebuild(src_file, obj_file, defines, flags):
                with self.lock:
                    self.stats["cached"] += 1
                    cached_count += 1
                continue
            
            # Construire la commande
            cmd = self._build_compile_command_hybrid(compiler, src_file, obj_file, 
                                                   includes, defines, flags)
            
            job = SimpleCompilationJob(
                job_id=i,
                command=cmd,
                source_file=src_file,
                object_file=obj_file,
                workspace_dir=self.workspace.location
            )
            
            compilation_jobs.append(job)
        
        # Afficher les statistiques de cache
        if cached_count > 0:
            if is_hidden_project:
                Reporter.detail(f"💾 {cached_count} file(s) up to date")
            else:
                Reporter.success(f"💾 {cached_count} file(s) up to date (cached)")
        
        # Exécuter la compilation avec la stratégie hybride
        if compilation_jobs:
            compile_start = time.time()
            
            # Choisir la stratégie en fonction du nombre de fichiers
            if len(compilation_jobs) > self.process_count * 2:
                # Beaucoup de fichiers : utiliser multiprocessing + threading
                success = self._execute_compilation_hybrid(compilation_jobs)
            else:
                # Peu de fichiers : utiliser threading seulement
                success = self._execute_compilation_threaded(compilation_jobs)
            
            compile_time = time.time() - compile_start
            self.stats["compilation_time"] += compile_time
            
            if not success:
                return False
            
            # Mettre à jour le cache
            if self.cache:
                for job in compilation_jobs:
                    if Path(job.object_file).exists():
                        self.cache.update(job.source_file, job.object_file, 
                                        defines, flags)
        
        # Prépare-link
        if project.prelinkcommands:
            if not self._execute_commands_sequential(project.prelinkcommands, expander):
                return False
        
        # Linkage
        object_files = [str(obj_dir / Path(src).with_suffix(".o").name) for src in source_files]
        output_file = self._get_output_path_hybrid(project, target_dir, expander)
        
        link_start = time.time()
        
        success = self._execute_linking_hybrid(project, toolchain, object_files, 
                                             output_file, lib_dirs, links, expander)
        
        link_time = time.time() - link_start
        self.stats["linking_time"] += link_time
        
        if not success:
            return False
        
        # Post-link
        if project.postlinkcommands:
            if not self._execute_commands_sequential(project.postlinkcommands, expander):
                return False
        
        # Copier les dépendances (sauf pour les projets cachés)
        if not is_hidden_project and project.kind in [ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP]:
            self._copy_dependency_libraries_hybrid(project, target_dir, expander)
        
        # Copier les fichiers dépendants
        if project.dependfiles:
            self._copy_depend_files_hybrid(project, target_dir, expander)
        
        # Post-build
        if project.postbuildcommands:
            if not self._execute_commands_sequential(project.postbuildcommands, expander):
                return False
        
        # Sauvegarder le cache
        if self.cache:
            self.cache.save()
        
        # Statistiques
        total_time = time.time() - total_start
        self.stats["total_time"] += total_time
        
        if is_hidden_project:
            Reporter.detail(f"🔧 Built hidden project: {output_file} ({total_time:.2f}s)")
        else:
            Reporter.success(f"✅ Built: {output_file} ({total_time:.2f}s)")
        
        return True
    
    def _execute_compilation_hybrid(self, jobs: List[SimpleCompilationJob]) -> bool:
        """Exécute la compilation avec stratégie hybride (processus + threads)"""
        
        total_jobs = len(jobs)
        Reporter.info(f"🔨 Compiling {total_jobs} file(s) with hybrid strategy...")
        
        # Diviser les jobs entre processus et threads
        process_jobs = jobs[:self.process_count]
        thread_jobs = jobs[self.process_count:]
        
        completed = 0
        failed_jobs = []
        results_queue = queue.Queue()
        
        # Fonction pour traiter les résultats
        def process_results():
            nonlocal completed, failed_jobs
            while completed < total_jobs:
                try:
                    job_id, success, message = results_queue.get(timeout=0.1)
                    
                    if success:
                        with self.lock:
                            self.stats["compiled"] += 1
                            completed += 1
                        
                        # Afficher la progression
                        progress_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
                        progress = progress_chars[completed % len(progress_chars)]
                        print(f"\r  {progress} [{completed}/{total_jobs}] {message}", end="", flush=True)
                    else:
                        with self.lock:
                            self.stats["failed"] += 1
                            completed += 1
                        
                        # Trouver le job correspondant
                        for job in jobs:
                            if job.job_id == job_id:
                                failed_jobs.append((job.source_file, message))
                                print(f"\r  ✗ {Path(job.source_file).name}: {message}")
                                break
                            
                except queue.Empty:
                    continue
        
        # Démarrer le thread de traitement des résultats
        results_thread = threading.Thread(target=process_results, daemon=True)
        results_thread.start()
        
        # Exécuter les jobs CPU intensifs avec des processus
        if process_jobs:
            try:
                with ProcessPoolExecutor(max_workers=min(len(process_jobs), self.process_count)) as executor:
                    future_to_job = {}
                    for job in process_jobs:
                        future = executor.submit(execute_simple_compilation_job, job)
                        future_to_job[future] = job.job_id
                    
                    for future in as_completed(future_to_job):
                        try:
                            result = future.result(timeout=310)
                            results_queue.put(result)
                        except Exception as e:
                            results_queue.put((future_to_job[future], False, str(e)))
                
                with self.lock:
                    self.stats["process_compiled"] += len(process_jobs)
                    
            except Exception as e:
                Display.warning(f"Process pool failed, falling back to threads: {e}")
                # Fallback: exécuter avec des threads
                thread_jobs.extend(process_jobs)
        
        # Exécuter les jobs I/O intensifs avec des threads
        if thread_jobs:
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                future_to_job = {}
                for job in thread_jobs:
                    future = executor.submit(execute_simple_compilation_job, job)
                    future_to_job[future] = job.job_id
                
                for future in as_completed(future_to_job):
                    try:
                        result = future.result(timeout=310)
                        results_queue.put(result)
                    except Exception as e:
                        results_queue.put((future_to_job[future], False, str(e)))
            
            with self.lock:
                self.stats["thread_compiled"] += len(thread_jobs)
        
        # Attendre que tous les résultats soient traités
        while results_thread.is_alive() and completed < total_jobs:
            time.sleep(0.1)
        
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
    
    def _execute_compilation_threaded(self, jobs: List[SimpleCompilationJob]) -> bool:
        """Exécute la compilation avec threading seulement"""
        
        total_jobs = len(jobs)
        if total_jobs == 0:
            return True
        
        Reporter.info(f"🔨 Compiling {total_jobs} file(s) with threading...")
        
        with ThreadPoolExecutor(max_workers=min(total_jobs, self.thread_count)) as executor:
            future_to_job = {}
            for job in jobs:
                future = executor.submit(execute_simple_compilation_job, job)
                future_to_job[future] = job
            
            completed = 0
            failed_jobs = []
            
            # Afficher la progression
            progress_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
            
            for future in as_completed(future_to_job):
                job = future_to_job[future]
                
                try:
                    job_id, success, message = future.result(timeout=310)
                    
                    if success:
                        with self.lock:
                            self.stats["compiled"] += 1
                            completed += 1
                            self.stats["thread_compiled"] += 1
                        
                        # Afficher la progression
                        progress = progress_chars[completed % len(progress_chars)]
                        print(f"\r  {progress} [{completed}/{total_jobs}] {message}", end="", flush=True)
                    else:
                        with self.lock:
                            self.stats["failed"] += 1
                            completed += 1
                        
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
    
    def _execute_linking_hybrid(self, project: Project, toolchain, object_files: List[str],
                               output_file: str, lib_dirs: List[str], links: List[str],
                               expander: VariableExpander) -> bool:
        """Exécute le linkage"""
        
        if project.name.startswith("__"):
            Reporter.detail("🔗 Linking hidden project...")
        else:
            Reporter.info("🔗 Linking...")
        
        linker = toolchain.linker or toolchain.compiler
        
        # Construire la commande de linkage
        cmd = self._build_link_command_hybrid(project, toolchain, object_files, output_file, 
                                            lib_dirs, links, expander)
        
        if not cmd:
            return False
        
        # Créer le job de linkage
        job = SimpleLinkingJob(
            job_id=0,
            command=cmd,
            project_name=project.name,
            output_file=output_file,
            workspace_dir=self.workspace.location
        )
        
        # Exécuter le linkage dans un thread séparé
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(execute_simple_linking_job, job)
            
            try:
                job_id, success, message = future.result(timeout=600)
                
                if success:
                    with self.lock:
                        self.stats["linked"] += 1
                    
                    if project.name.startswith("__"):
                        Reporter.detail(f"  ✓ {message}")
                    else:
                        Reporter.success(f"  ✓ {message}")
                    return True
                else:
                    Display.error(f"✗ Linking failed for {project.name}: {message}")
                    return False
                    
            except Exception as e:
                Display.error(f"✗ Linking error for {project.name}: {e}")
                return False
    
    def _build_compile_command_hybrid(self, compiler: str, source_file: str, object_file: str,
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
        
        return cmd
    
    def _build_link_command_hybrid(self, project: Project, toolchain, object_files: List[str],
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
                    # Inclure les projets cachés dans les liens
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
    
    def _resolve_source_files_hybrid(self, project: Project, expander: VariableExpander) -> List[str]:
        """Résolution des fichiers sources avec support des projets cachés"""
        
        base_dir = project.location or self.workspace.location
        
        # Résolution des patterns
        all_files = resolve_file_list(project.files, base_dir, expander)
        
        # Filtrer les fichiers source uniquement
        source_extensions = {'.c', '.cpp', '.cc', '.cxx', '.m', '.mm'}
        source_files = [f for f in all_files if Path(f).suffix.lower() in source_extensions]
        
        # Exclusions (sauf pour les projets cachés qui peuvent avoir leurs propres règles)
        if project.excludefiles:
            exclude_files = set(resolve_file_list(project.excludefiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_files]
        
        # Exclusions de main pour les tests
        if project.is_test and project.excludemainfiles:
            exclude_mains = set(resolve_file_list(project.excludemainfiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_mains]
        
        return source_files
    
    def _resolve_dependencies_hybrid(self, project: Project, expander: VariableExpander) -> Tuple[List, List, List]:
        """Résolution des dépendances INCLUANT les projets cachés"""
        
        includes = list(project.includedirs)
        lib_dirs = list(project.libdirs)
        links = list(project.links)
        
        # Liens spécifiques à la plateforme
        if self.platform in project.system_links:
            links.extend(project.system_links[self.platform])
        
        # Dépendances du projet (INCLURE les projets cachés comme __Unitest__)
        for dep_name in project.dependson:
            if dep_name in self.workspace.projects:
                dep = self.workspace.projects[dep_name]
                includes.extend(dep.includedirs)
                
                if dep.targetdir:
                    lib_dirs.append(expander.expand(dep.targetdir))
                
                # Ajouter le nom de la bibliothèque cachée
                links.append(dep.targetname or dep.name)
        
        # Expansion des variables
        includes = [expander.expand(inc) for inc in includes]
        lib_dirs = [expander.expand(lib) for lib in lib_dirs]
        links = [expander.expand(link) for link in links]
        
        return includes, lib_dirs, links
    
    def _get_defines_hybrid(self, project: Project, toolchain, expander: VariableExpander) -> List[str]:
        """Récupération des définitions"""
        
        defines = []
        defines.extend(toolchain.defines)
        defines.extend(project.defines)
        
        # Définitions filtrées
        for filter_expr, filter_defines in project._filtered_defines.items():
            if self._filter_matches(filter_expr):
                defines.extend(filter_defines)
        
        return [expander.expand(d) for d in defines]
    
    def _get_compiler_flags_hybrid(self, project: Project, toolchain, expander: VariableExpander) -> List[str]:
        """Récupération des flags"""
        
        flags = []
        
        # Détecter MSVC
        compiler = self._get_compiler_hybrid(toolchain, project.language.value == "C++")
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
    
    def _get_output_path_hybrid(self, project: Project, target_dir: Path, 
                               expander: VariableExpander) -> str:
        """Chemin de sortie"""
        
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
    
    def _get_compiler_hybrid(self, toolchain, is_cpp: bool) -> str:
        """Récupération du compilateur"""
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
    
    def _copy_dependency_libraries_hybrid(self, project: Project, target_dir: Path, expander: VariableExpander):
        """Copie des bibliothèques de dépendances (INCLURE les projets cachés)"""
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
    
    def _copy_depend_files_hybrid(self, project: Project, target_dir: Path, expander: VariableExpander):
        """Copie des fichiers dépendants"""
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
        Reporter.info(f"  Compiled:      {self.stats['compiled']} files")
        Reporter.info(f"    • Processes:  {self.stats['process_compiled']}")
        Reporter.info(f"    • Threads:    {self.stats['thread_compiled']}")
        Reporter.info(f"  Cached:        {self.stats['cached']} files")
        Reporter.info(f"  Linked:        {self.stats['linked']} targets")
        
        if self.stats['failed'] > 0:
            Reporter.info(f"  Failed:        {self.stats['failed']} files")
        
        Reporter.info(f"  Total time:    {self.stats['total_time']:.2f}s")
        Reporter.info(f"  Compile time:  {self.stats['compilation_time']:.2f}s")
        Reporter.info(f"  Link time:     {self.stats['linking_time']:.2f}s")
        
        # Calculer la vitesse
        if self.stats['compiled'] > 0 and self.stats['compilation_time'] > 0:
            speed = self.stats['compiled'] / self.stats['compilation_time']
            Reporter.info(f"  Compile speed: {speed:.1f} files/second")