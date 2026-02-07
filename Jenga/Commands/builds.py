#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Build with Generation
Version ultra-rapide avec génération préalable
"""

import sys
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from core.generator import FastGenerator, BuildManifest
from utils.reporter import Reporter
from utils.display import Display


class GeneratedBuildSystem:
    """Système de build basé sur la génération"""
    
    def __init__(self, workspace, config: str, platform: str, jobs: int = None):
        self.workspace = workspace
        self.config = config
        self.platform = platform
        self.jobs = jobs or max(1, multiprocessing.cpu_count())
        
        # Générateur
        self.generator = FastGenerator(workspace, platform)
        
        # Statistiques
        self.stats = {
            "generated": 0,
            "compiled": 0,
            "cached": 0,
            "failed": 0,
            "linked": 0,
            "total_time": 0.0,
            "generation_time": 0.0,
            "compilation_time": 0.0,
            "linking_time": 0.0
        }

    # Ajoutez cette méthode pour vérifier les chemins
    def _validate_paths(self, manifest: BuildManifest) -> bool:
        """Valide que tous les chemins nécessaires existent"""
        
        # Vérifier les répertoires
        missing_dirs = []
        
        for cmd in manifest.compile_commands:
            # Vérifier le répertoire des objets
            obj_dir = Path(cmd.object).parent
            if not obj_dir.exists():
                missing_dirs.append(str(obj_dir))
        
        # Vérifier le répertoire de sortie
        if manifest.link_command:
            output_dir = Path(manifest.link_command.output).parent
            if not output_dir.exists():
                missing_dirs.append(str(output_dir))
        
        # Créer les répertoires manquants
        if missing_dirs:
            Display.warning(f"Creating {len(missing_dirs)} missing directory(ies)")
            for dir_path in missing_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                Reporter.detail(f"  Created: {dir_path}")
        
        return True
    
    def build_project(self, project_name: str, toolchain: str = "default", 
                    force_regenerate: bool = False) -> bool:
        """Build un projet avec génération"""
        
        if project_name not in self.workspace.projects:
            Display.error(f"Project not found: {project_name}")
            return False
        
        project = self.workspace.projects[project_name]
        is_hidden = project_name.startswith("__")
        
        total_start = time.time()
        
        if is_hidden:
            Reporter.section(f"Building hidden project: {project_name}")
        else:
            Reporter.section(f"Building project: {project_name}")
        
        # ÉTAPE 1: Génération
        gen_start = time.time()
        
        manifest = self.generator.load_manifest(project_name, self.config, self.platform)
        needs_gen = force_regenerate
        
        if manifest and not force_regenerate:
            needs_gen = self.generator.manifest_needs_regeneration(
                manifest, project, self.config, self.platform, toolchain
            )
        
        if not manifest or needs_gen:
            if is_hidden:
                Reporter.info("Generating build manifest...")
            else:
                Reporter.info("📝 Generating build manifest...")
            
            manifest = self.generator.generate_for_project(
                project, self.config, self.platform, toolchain
            )
            
            self.stats["generated"] += 1
        
        gen_time = time.time() - gen_start
        self.stats["generation_time"] += gen_time
        
        # VALIDER LES CHEMINS AVANT DE CONTINUER
        if not self._validate_paths(manifest):
            Display.error("Failed to validate/create required directories")
            return False
        
        # ÉTAPE 2: Exécuter les commandes pré-build
        if manifest.prebuild_commands:
            if not self._run_commands(manifest.prebuild_commands, "pre-build"):
                return False
        
        # ÉTAPE 3: Compilation parallèle
        compile_start = time.time()
        
        if manifest.compile_commands:
            if is_hidden:
                Reporter.info(f"Compiling {len(manifest.compile_commands)} file(s)...")
            else:
                Reporter.info(f"🔨 Compiling {len(manifest.compile_commands)} file(s)...")
            
            success = self._execute_compilation(manifest)
            if not success:
                return False
        
        compile_time = time.time() - compile_start
        self.stats["compilation_time"] += compile_time
        
        # ÉTAPE 4: Linkage
        link_start = time.time()
        
        if manifest.link_command:
            if is_hidden:
                Reporter.info("Linking...")
            else:
                Reporter.info("🔗 Linking...")
            
            success = self._execute_linking(manifest)
            if not success:
                return False
        
        link_time = time.time() - link_start
        self.stats["linking_time"] += link_time
        
        # ÉTAPE 5: Commandes post-build
        if manifest.postbuild_commands:
            if not self._run_commands(manifest.postbuild_commands, "post-build"):
                return False
        
        # Fin
        total_time = time.time() - total_start
        self.stats["total_time"] += total_time
        
        if is_hidden:
            Reporter.detail(f"Built: {manifest.link_command.output if manifest.link_command else 'N/A'}")
        else:
            Reporter.success(f"✅ Built: {manifest.link_command.output if manifest.link_command else 'N/A'} ({total_time:.2f}s)")
        
        return True
    
    def _execute_compilation(self, manifest: BuildManifest) -> bool:
        """Exécute la compilation en parallèle avec ThreadPoolExecutor"""
        
        # Filtrer les fichiers à compiler
        tasks = []
        
        for cmd in manifest.compile_commands:
            if self._needs_compilation(cmd):
                tasks.append(cmd)
            else:
                self.stats["cached"] += 1
        
        if not tasks:
            cached_count = len(manifest.compile_commands)
            Reporter.success(f"💾 All {cached_count} files up to date")
            return True
        
        # Compilation parallèle
        total = len(tasks)
        compiled = 0
        failed = []
        lock = threading.Lock()
        
        def compile_single(cmd):
            """Compile un fichier unique"""
            try:
                start = time.time()
                
                result = subprocess.run(
                    cmd.command,
                    capture_output=True,
                    text=True,
                    cwd=self.workspace.location,
                    timeout=60
                )
                
                elapsed = time.time() - start
                
                if result.returncode == 0:
                    return (True, cmd.source, elapsed, "")
                else:
                    error = result.stderr if result.stderr else result.stdout
                    return (False, cmd.source, elapsed, error[:500])
                    
            except Exception as e:
                return (False, cmd.source, 0, str(e))
        
        # Exécution parallèle
        with ThreadPoolExecutor(max_workers=self.jobs) as executor:
            future_to_cmd = {executor.submit(compile_single, cmd): cmd for cmd in tasks}
            
            for future in as_completed(future_to_cmd):
                success, source, elapsed, error = future.result()
                
                with lock:
                    if success:
                        self.stats["compiled"] += 1
                        compiled += 1
                        
                        # Afficher progression
                        filename = Path(source).name
                        percent = (compiled / total) * 100
                        print(f"\r  [{compiled}/{total}] {percent:.0f}% {filename} ({elapsed:.2f}s)", 
                              end="", flush=True)
                    else:
                        self.stats["failed"] += 1
                        compiled += 1
                        failed.append((source, error))
                        print(f"\r  ✗ {Path(source).name}: {error[:100]}", flush=True)
        
        print()  # Nouvelle ligne
        
        # Gérer les erreurs
        if failed:
            Display.error(f"\n❌ {len(failed)} compilation(s) failed:")
            for source, error in failed[:3]:  # Afficher seulement les 3 premières
                Display.error(f"  {Path(source).name}: {error[:200]}")
            if len(failed) > 3:
                Display.error(f"  ... and {len(failed) - 3} more errors")
            return False
        
        return True
    
    def _needs_compilation(self, cmd) -> bool:
        """Vérifie si un fichier a besoin d'être compilé"""
        
        obj_path = Path(cmd.object)
        
        # Pas de fichier objet
        if not obj_path.exists():
            return True
        
        obj_mtime = obj_path.stat().st_mtime
        
        # Fichier source modifié
        src_path = Path(cmd.source)
        if src_path.exists() and src_path.stat().st_mtime > obj_mtime:
            return True
        
        # Dépendances modifiées
        for dep in cmd.dependencies:
            dep_path = Path(dep)
            if dep_path.exists() and dep_path.stat().st_mtime > obj_mtime:
                return True
        
        return False
    
    def _execute_linking(self, manifest: BuildManifest) -> bool:
        """Exécute le linkage avec meilleure gestion des erreurs"""
        
        if not manifest.link_command:
            return True
        
        cmd = manifest.link_command
        
        try:
            # CRÉER LE RÉPERTOIRE DE SORTIE AVANT LE LINKAGE
            output_path = Path(cmd.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            start = time.time()
            
            Reporter.detail(f"  Link command: {' '.join(cmd.command[:10])}{'...' if len(cmd.command) > 10 else ''}")
            Reporter.detail(f"  Output: {output_path}")
            
            result = subprocess.run(
                cmd.command,
                capture_output=True,
                text=True,
                cwd=self.workspace.location,
                timeout=300
            )
            
            elapsed = time.time() - start
            
            if result.returncode == 0:
                self.stats["linked"] += 1
                
                # Vérifier que le fichier a été créé
                if output_path.exists():
                    Reporter.success(f"  ✓ Linked ({elapsed:.2f}s) -> {output_path.name}")
                    return True
                else:
                    Display.error(f"✗ Link succeeded but output file not created: {output_path}")
                    return False
            else:
                error = result.stderr if result.stderr else result.stdout
                Display.error(f"✗ Linking failed:")
                
                # Afficher des informations utiles
                print(f"  Command: {' '.join(cmd.command)}")
                print(f"  Output path: {output_path}")
                print(f"  Output dir exists: {output_path.parent.exists()}")
                
                if error:
                    # Parser les erreurs de lien
                    lines = error.split('\n')
                    for line in lines[:10]:  # Afficher seulement les 10 premières lignes
                        if line.strip():
                            print(f"  {line}")
                
                return False
                
        except FileNotFoundError as e:
            Display.error(f"✗ Linker not found: {e}")
            # Essayer de trouver quel exécutable est manquant
            if cmd.command and len(cmd.command) > 0:
                print(f"  First command part: {cmd.command[0]}")
            return False
        except Exception as e:
            Display.error(f"✗ Linking error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _run_commands(self, commands: List[List[str]], context: str) -> bool:
        """Exécute des commandes"""
        for cmd_parts in commands:
            if not cmd_parts:
                continue
            
            cmd_str = " ".join(cmd_parts)
            Reporter.detail(f"  > {cmd_str}")
            
            try:
                result = subprocess.run(
                    cmd_str,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.workspace.location
                )
                
                if result.returncode != 0:
                    Display.error(f"{context} command failed: {cmd_str}")
                    if result.stderr:
                        print(result.stderr[:200])
                    return False
                    
            except Exception as e:
                Display.error(f"{context} command error: {e}")
                return False
        
        return True
    
    def print_stats(self):
        """Affiche les statistiques"""
        Reporter.section("Build Statistics")
        Reporter.info(f"  Generated:    {self.stats['generated']} manifest(s)")
        Reporter.info(f"  Compiled:     {self.stats['compiled']} files")
        Reporter.info(f"  Cached:       {self.stats['cached']} files")
        Reporter.info(f"  Linked:       {self.stats['linked']} targets")
        
        if self.stats['failed'] > 0:
            Reporter.info(f"  Failed:       {self.stats['failed']} files")
        
        Reporter.info(f"  Total time:   {self.stats['total_time']:.2f}s")
        Reporter.info(f"  Generation:   {self.stats['generation_time']:.2f}s")
        Reporter.info(f"  Compilation:  {self.stats['compilation_time']:.2f}s")
        Reporter.info(f"  Linking:      {self.stats['linking_time']:.2f}s")
        
        if self.stats['compiled'] > 0 and self.stats['compilation_time'] > 0:
            speed = self.stats['compiled'] / self.stats['compilation_time']
            Reporter.info(f"  Compile speed: {speed:.1f} files/second")


def execute(options: dict) -> bool:
    """Commande build avec génération"""
    
    Reporter.start()
    
    # Charger workspace
    workspace = load_workspace()
    if not workspace:
        return False
    
    # Options
    config = options.get("config", "Debug")
    platform = options.get("platform", "Windows")
    project_name = options.get("project", None)
    toolchain = options.get("toolchain", "default")
    jobs = int(options.get("jobs", 0)) or None
    force_gen = options.get("force_generate", False)
    clean = options.get("clean", False)
    
    # Nettoyage
    if clean:
        gen_dir = Path(workspace.location) / ".cjenga"
        if gen_dir.exists():
            import shutil
            shutil.rmtree(gen_dir)
            Display.info("🧹 Cleared generated files")
    
    # Validation
    if config not in workspace.configurations:
        Display.error(f"Invalid configuration: {config}")
        return False
    
    if platform not in workspace.platforms:
        Display.error(f"Invalid platform: {platform}")
        return False
    
    # Créer le système
    builder = GeneratedBuildSystem(workspace, config, platform, jobs)
    
    # Build
    if project_name:
        success = builder.build_project(project_name, toolchain, force_gen)
    else:
        # Tous les projets
        order = get_build_order(workspace)
        
        if not order:
            return False
        
        Display.info(f"Building {len(order)} project(s)")
        Display.info(f"Order: {' → '.join([p for p in order if not p.startswith('__')])}")
        
        for name in order:
            if not builder.build_project(name, toolchain, force_gen):
                return False
    
    # Statistiques
    builder.print_stats()
    
    Reporter.end()
    
    if builder.stats['failed'] == 0:
        Display.success("✅ Build completed successfully")
    else:
        Display.error("❌ Build completed with errors")
    
    return builder.stats['failed'] == 0


def get_build_order(workspace) -> list:
    """Ordre de build"""
    
    graph = {}
    in_degree = {}
    
    for name, project in workspace.projects.items():
        deps = [d for d in project.dependson if d in workspace.projects]
        graph[name] = deps
        in_degree[name] = len(deps)
    
    # Tri topologique
    queue = [name for name, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        queue.sort()
        current = queue.pop(0)
        result.append(current)
        
        for name in graph:
            if current in graph[name]:
                in_degree[name] -= 1
                if in_degree[name] == 0:
                    queue.append(name)
    
    # Vérifier circulaire
    if len(result) != len(graph):
        Display.error("Circular dependency detected")
        return []
    
    return result


if __name__ == "__main__":
    # Test
    execute({})