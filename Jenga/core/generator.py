#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Fast Generator
Génère des fichiers intermédiaires pour une compilation ultra-rapide
"""

import os
import sys
import json
import hashlib
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set, Optional
from dataclasses import dataclass, field, asdict
import time

try:
    from .api import Project, ProjectKind, Workspace, Optimization, Toolchain
    from .variables import VariableExpander, resolve_file_list, expand_path_patterns
except ImportError:
    from core.api import Project, ProjectKind, Workspace, Optimization, Toolchain
    from core.variables import VariableExpander, resolve_file_list, expand_path_patterns


@dataclass
class GeneratedCommand:
    """Commande de compilation générée"""
    source: str
    object: str
    command: List[str]
    dependencies: List[str] = field(default_factory=list)
    defines: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)


@dataclass
class GeneratedLinkCommand:
    """Commande de linkage générée"""
    output: str
    objects: List[str]
    command: List[str]
    libraries: List[str] = field(default_factory=list)
    lib_dirs: List[str] = field(default_factory=list)


@dataclass
class BuildManifest:
    """Manifest de build complet pour un projet"""
    project_name: str
    config: str
    platform: str
    compile_commands: List[GeneratedCommand] = field(default_factory=list)
    link_command: Optional[GeneratedLinkCommand] = None
    prebuild_commands: List[List[str]] = field(default_factory=list)
    postbuild_commands: List[List[str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    generated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dict pour JSON"""
        return {
            "project": self.project_name,
            "config": self.config,
            "platform": self.platform,
            "compile_commands": [
                {
                    "source": cmd.source,
                    "object": cmd.object,
                    "command": cmd.command,
                    "dependencies": cmd.dependencies,
                    "defines": cmd.defines,
                    "includes": cmd.includes
                }
                for cmd in self.compile_commands
            ],
            "link_command": {
                "output": self.link_command.output,
                "objects": self.link_command.objects,
                "command": self.link_command.command,
                "libraries": self.link_command.libraries,
                "lib_dirs": self.link_command.lib_dirs
            } if self.link_command else None,
            "prebuild_commands": self.prebuild_commands,
            "postbuild_commands": self.postbuild_commands,
            "dependencies": self.dependencies,
            "generated_at": self.generated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BuildManifest':
        """Créer depuis dict"""
        manifest = cls(
            project_name=data["project"],
            config=data["config"],
            platform=data["platform"],
            prebuild_commands=data.get("prebuild_commands", []),
            postbuild_commands=data.get("postbuild_commands", []),
            dependencies=data.get("dependencies", []),
            generated_at=data.get("generated_at", time.time())
        )
        
        # Commands de compilation
        for cmd_data in data.get("compile_commands", []):
            cmd = GeneratedCommand(
                source=cmd_data["source"],
                object=cmd_data["object"],
                command=cmd_data["command"],
                dependencies=cmd_data.get("dependencies", []),
                defines=cmd_data.get("defines", []),
                includes=cmd_data.get("includes", [])
            )
            manifest.compile_commands.append(cmd)
        
        # Commande de linkage
        if data.get("link_command"):
            link_data = data["link_command"]
            manifest.link_command = GeneratedLinkCommand(
                output=link_data["output"],
                objects=link_data["objects"],
                command=link_data["command"],
                libraries=link_data.get("libraries", []),
                lib_dirs=link_data.get("lib_dirs", [])
            )
        
        return manifest


class FastGenerator:
    """Générateur de fichiers intermédiaires ultra-rapide"""
    
    def __init__(self, workspace: Workspace, platform: str = None):
        self.workspace = workspace
        self.platform = platform or self._detect_platform()
        self.generation_dir = Path(workspace.location) / ".cjenga"
        self.generation_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache des dépendances analysées
        self.dep_cache: Dict[str, List[str]] = {}
        self.header_cache: Dict[str, List[str]] = {}
        self._analyzing = set()  # Pour éviter les cycles
    
    def _detect_platform(self) -> str:
        """Détecte la plateforme courante"""
        import platform as sys_platform
        system = sys_platform.system()
        
        if system == "Windows":
            return "Windows"
        elif system == "Darwin":
            return "MacOS"
        elif system == "Linux":
            return "Linux"
        else:
            return system
    
    def generate_for_project(self, project: Project, config: str, 
                        platform: str, toolchain_name: str = "default") -> BuildManifest:
        """Génère un manifest de build pour un projet"""
        
        print(f"🔨 Generating build manifest for {project.name} ({config}/{platform})...")
        
        # Récupérer toolchain
        if project.toolchain:
            toolchain_name = project.toolchain
        
        toolchain = self.workspace.toolchains[toolchain_name]
        
        # Expander
        expander = VariableExpander(self.workspace, project, config, platform)
        
        # Résoudre les dépendances
        includes, lib_dirs, links = self._resolve_all_dependencies(
            project, expander, config, platform
        )
        
        # Résoudre TOUS les fichiers sources
        all_source_files = self._resolve_all_source_files(project, expander)
        
        print(f"  📁 Found {len(all_source_files)} source files")
        print(f"  📂 {len(includes)} include directories")
        
        # Récupérer les paramètres
        defines = self._get_all_defines(project, toolchain, expander, config, platform)
        flags = self._get_all_flags(project, toolchain, expander, config, platform)
        
        # Répertoires de sortie - CRÉER LES RÉPERTOIRES
        obj_dir = Path(expander.expand(project.objdir))
        target_dir = Path(expander.expand(project.targetdir))
        
        # CRÉER LES RÉPERTOIRES ICI
        obj_dir.mkdir(parents=True, exist_ok=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"  📂 Created output directories:")
        print(f"    - Objects: {obj_dir}")
        print(f"    - Target: {target_dir}")
        
        # Générer les commandes de compilation
        compile_commands = []
        
        for src_file in all_source_files:
            src_path = Path(src_file)
            obj_file = str(obj_dir / src_path.with_suffix(".o").name)
            
            # Déterminer le compilateur
            is_cpp = src_path.suffix in ['.cpp', '.cc', '.cxx', '.hpp', '.inl']
            compiler = self._get_compiler(toolchain, is_cpp)
            
            # Construire la commande
            cmd = self._build_compile_command(compiler, src_file, obj_file, 
                                            includes, defines, flags)
            
            # Analyser les dépendances (headers)
            dependencies = self._analyze_dependencies(src_file, includes)
            
            compile_cmd = GeneratedCommand(
                source=src_file,
                object=obj_file,
                command=cmd,
                dependencies=dependencies,
                defines=defines,
                includes=includes
            )
            
            compile_commands.append(compile_cmd)
        
        # Générer la commande de linkage
        object_files = [str(obj_dir / Path(src).with_suffix(".o").name) for src in all_source_files]
        output_file = self._get_output_path(project, target_dir, expander)
        
        link_command = self._build_link_command(project, toolchain, object_files, 
                                              output_file, lib_dirs, links, expander)
        
        # Commandes pré/post
        prebuild_commands = []
        postbuild_commands = []
        
        for cmd_tpl in project.prebuildcommands:
            if isinstance(cmd_tpl, str):
                cmd = expander.expand(cmd_tpl)
                prebuild_commands.append([cmd] if ' ' not in cmd else cmd.split())
            else:
                cmd = [expander.expand(part) for part in cmd_tpl]
                prebuild_commands.append(cmd)
        
        for cmd_tpl in project.postbuildcommands:
            if isinstance(cmd_tpl, str):
                cmd = expander.expand(cmd_tpl)
                postbuild_commands.append([cmd] if ' ' not in cmd else cmd.split())
            else:
                cmd = [expander.expand(part) for part in cmd_tpl]
                postbuild_commands.append(cmd)
        
        # Créer le manifest
        manifest = BuildManifest(
            project_name=project.name,
            config=config,
            platform=platform,
            compile_commands=compile_commands,
            link_command=link_command,
            prebuild_commands=prebuild_commands,
            postbuild_commands=postbuild_commands,
            dependencies=project.dependson.copy()
        )
        
        # Sauvegarder
        self._save_manifest(manifest)
        
        print(f"  ✅ Generated {len(compile_commands)} compile commands")
        print(f"  🔗 Generated link command for {output_file}")
        
        return manifest
    
    def _save_manifest(self, manifest: BuildManifest):
        """Sauvegarde le manifest sur disque"""
        manifest_file = self.generation_dir / f"{manifest.project_name}_{manifest.config}_{manifest.platform}.json"
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        
        # Sauvegarder aussi le hash du projet
        hash_file = manifest_file.with_suffix(".hash")
        with open(hash_file, 'w') as f:
            project_hash = self._get_project_hash(
                manifest.project_name, 
                manifest.config,
                manifest.platform
            )
            f.write(project_hash)
    
    def load_manifest(self, project_name: str, config: str, platform: str) -> Optional[BuildManifest]:
        """Charge un manifest depuis le disque"""
        manifest_file = self.generation_dir / f"{project_name}_{config}_{platform}.json"
        
        if not manifest_file.exists():
            return None
        
        try:
            with open(manifest_file, 'r') as f:
                data = json.load(f)
            
            return BuildManifest.from_dict(data)
        except Exception as e:
            print(f"⚠️ Failed to load manifest: {e}")
            return None
    
    def manifest_needs_regeneration(self, manifest: BuildManifest, project: Project,
                                  config: str, platform: str, toolchain_name: str) -> bool:
        """Vérifie si le manifest doit être régénéré"""
        
        # Vérifier la date de génération
        manifest_file = self.generation_dir / f"{manifest.project_name}_{manifest.config}_{manifest.platform}.json"
        
        if not manifest_file.exists():
            return True
        
        # Vérifier si le projet a changé
        project_hash = self._get_project_hash(project.name, config, platform)
        manifest_hash_file = manifest_file.with_suffix(".hash")
        
        if manifest_hash_file.exists():
            try:
                with open(manifest_hash_file, 'r') as f:
                    saved_hash = f.read().strip()
                
                if saved_hash != project_hash:
                    return True
            except:
                return True
        else:
            return True
        
        # Vérifier si les fichiers sources ont changé
        for compile_cmd in manifest.compile_commands:
            src_file = Path(compile_cmd.source)
            if src_file.exists():
                # Vérifier la date de modification
                src_mtime = src_file.stat().st_mtime
                if src_mtime > manifest.generated_at:
                    return True
                
                # Vérifier les dépendances
                for dep in compile_cmd.dependencies:
                    dep_path = Path(dep)
                    if dep_path.exists() and dep_path.stat().st_mtime > manifest.generated_at:
                        return True
        
        return False
    
    def _get_project_hash(self, project_name: str, config: str, platform: str) -> str:
        """Calcule un hash du projet pour détecter les changements"""
        hasher = hashlib.md5()
        
        if project_name not in self.workspace.projects:
            return ""
        
        project = self.workspace.projects[project_name]
        
        # Toolchain
        toolchain_name = project.toolchain or "default"
        hasher.update(toolchain_name.encode())
        
        # Config et platform
        hasher.update(config.encode())
        hasher.update(platform.encode())
        
        # Paramètres du projet
        hasher.update(project.name.encode())
        hasher.update(project.kind.value.encode())
        hasher.update(project.language.value.encode())
        
        # Dépendances
        for dep in sorted(project.dependson):
            hasher.update(dep.encode())
        
        # Inclure les paramètres de la toolchain
        if toolchain_name in self.workspace.toolchains:
            toolchain = self.workspace.toolchains[toolchain_name]
            for d in sorted(toolchain.defines):
                hasher.update(d.encode())
            for f in sorted(toolchain.cflags):
                hasher.update(f.encode())
            for f in sorted(toolchain.cxxflags):
                hasher.update(f.encode())
            for f in sorted(toolchain.ldflags):
                hasher.update(f.encode())
        
        return hasher.hexdigest()
    
    def _analyze_dependencies(self, source_file: str, include_dirs: List[str]) -> List[str]:
        """Analyse un fichier source pour trouver ses dépendances (headers)"""
        
        # Utiliser le cache
        cache_key = f"{source_file}:{':'.join(sorted(include_dirs))}"
        if cache_key in self.dep_cache:
            return self.dep_cache[cache_key]
        
        dependencies = []
        source_path = Path(source_file)
        
        if not source_path.exists():
            self.dep_cache[cache_key] = []
            return []
        
        try:
            # Lire seulement le début du fichier
            with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(65536)
            
            # Chercher les includes
            import re
            includes = re.findall(r'#include\s+["<]([^">]+)[">]', content)
            
            for inc in includes:
                # Chercher le header
                header_path = self._find_header(inc, include_dirs, source_path.parent)
                if header_path and header_path.exists():
                    dep_path = str(header_path)
                    if dep_path not in dependencies:
                        dependencies.append(dep_path)
                        
                        # Analyser récursivement (avec limite)
                        if len(dependencies) < 50 and dep_path not in self._analyzing:
                            self._analyzing.add(dep_path)
                            try:
                                sub_deps = self._analyze_dependencies(dep_path, include_dirs)
                                for d in sub_deps:
                                    if d not in dependencies:
                                        dependencies.append(d)
                            finally:
                                self._analyzing.discard(dep_path)
            
            # Dédupliquer
            dependencies = list(set(dependencies))
            
        except Exception as e:
            print(f"⚠️ Failed to analyze dependencies for {source_file}: {e}")
        
        # Mettre en cache
        self.dep_cache[cache_key] = dependencies
        
        return dependencies
    
    def _find_header(self, header_name: str, include_dirs: List[str], 
                    source_dir: Path) -> Optional[Path]:
        """Trouve un header dans les répertoires d'inclusion"""
        
        # Chercher dans le répertoire source d'abord
        candidate = source_dir / header_name
        if candidate.exists():
            return candidate
        
        # Chercher dans les include_dirs
        for inc_dir in include_dirs:
            candidate = Path(inc_dir) / header_name
            if candidate.exists():
                return candidate
        
        return None
    
    def _resolve_all_source_files(self, project: Project, expander: VariableExpander) -> List[str]:
        """Résout TOUS les fichiers sources avec analyse approfondie"""
        
        base_dir = project.location or self.workspace.location
        
        # Résoudre les patterns
        all_files = resolve_file_list(project.files, base_dir, expander)
        
        # Filtrer pour garder seulement les sources
        source_extensions = {'.c', '.cpp', '.cc', '.cxx', '.m', '.mm'}
        source_files = [f for f in all_files if Path(f).suffix.lower() in source_extensions]
        
        # Exclure les fichiers spécifiés
        if project.excludefiles:
            exclude_files = set(resolve_file_list(project.excludefiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_files]
        
        # Pour les tests, exclure les fichiers main
        if project.is_test and project.excludemainfiles:
            exclude_mains = set(resolve_file_list(project.excludemainfiles, base_dir, expander))
            source_files = [f for f in source_files if f not in exclude_mains]
        
        return source_files
    
    def _resolve_all_dependencies(self, project: Project, expander: VariableExpander,
                                config: str, platform: str) -> Tuple[List[str], List[str], List[str]]:
        """Résout TOUTES les dépendances de manière exhaustive"""
        
        includes = list(project.includedirs)
        lib_dirs = list(project.libdirs)
        links = list(project.links)
        
        # Liens système
        if platform in project.system_links:
            links.extend(project.system_links[platform])
        
        # Dépendances du projet (récursif)
        visited = set()
        
        def resolve_deps(proj_name: str):
            if proj_name in visited:
                return
            visited.add(proj_name)
            
            if proj_name in self.workspace.projects:
                dep = self.workspace.projects[proj_name]
                
                # Ajouter les includes
                includes.extend(dep.includedirs)
                
                # Ajouter les lib_dirs
                if dep.targetdir:
                    lib_dirs.append(expander.expand(dep.targetdir))
                
                # Ajouter les liens
                links.append(dep.targetname or dep.name)
                
                # Résoudre récursivement
                for sub_dep in dep.dependson:
                    resolve_deps(sub_dep)
        
        # Résoudre toutes les dépendances
        for dep_name in project.dependson:
            resolve_deps(dep_name)
        
        # Dédupliquer
        includes = list(set(includes))
        lib_dirs = list(set(lib_dirs))
        links = list(set(links))
        
        # Expansion
        includes = [expander.expand(inc) for inc in includes]
        lib_dirs = [expander.expand(lib) for lib in lib_dirs]
        links = [expander.expand(link) for link in links]
        
        return includes, lib_dirs, links
    
    def _get_all_defines(self, project: Project, toolchain: Toolchain,
                        expander: VariableExpander, config: str, platform: str) -> List[str]:
        """Récupère TOUTES les définitions"""
        
        defines = []
        defines.extend(toolchain.defines)
        defines.extend(project.defines)
        
        # Définitions de configuration
        defines.append(f"BUILD_{config.upper()}")
        defines.append(f"PLATFORM_{platform.upper()}")
        
        # Définitions filtrées
        for filter_expr, filter_defines in project._filtered_defines.items():
            if self._filter_matches(filter_expr, config, platform):
                defines.extend(filter_defines)
        
        # Expansion
        defines = [expander.expand(d) for d in defines]
        
        return list(set(defines))
    
    def _get_all_flags(self, project: Project, toolchain: Toolchain,
                    expander: VariableExpander, config: str, platform: str) -> List[str]:
        """Récupère TOUS les flags avec support C++23"""
        
        flags = []
        
        # Détecter le compilateur
        compiler = self._get_compiler(toolchain, project.language.value == "C++")
        is_msvc = "cl.exe" in compiler.lower() or "cl" == compiler.lower()
        is_clang = "clang" in compiler.lower()
        is_gcc = "gcc" in compiler.lower() or "g++" in compiler.lower()
        
        # Standard C++
        if project.language.value == "C++":
            if is_msvc:
                # MSVC
                if "23" in project.cppdialect or "2b" in project.cppdialect:
                    flags.append("/std:c++latest")  # MSVC n'a pas encore C++23 officiel
                elif "20" in project.cppdialect:
                    flags.append("/std:c++20")
                elif "17" in project.cppdialect:
                    flags.append("/std:c++17")
                elif "14" in project.cppdialect:
                    flags.append("/std:c++14")
                elif "11" in project.cppdialect:
                    flags.append("/std:c++11")
            else:
                # GCC/Clang
                if "23" in project.cppdialect or "2b" in project.cppdialect:
                    if is_clang and "clang" in compiler and "++" in compiler:
                        flags.append("-std=c++2b")  # Clang utilise c++2b
                    else:
                        flags.append("-std=c++23")
                elif "20" in project.cppdialect:
                    flags.append("-std=c++20")
                elif "17" in project.cppdialect:
                    flags.append("-std=c++17")
                elif "14" in project.cppdialect:
                    flags.append("-std=c++14")
                elif "11" in project.cppdialect:
                    flags.append("-std=c++11")
                else:
                    # Par défaut
                    flags.append("-std=c++17")
        
        # Standard C
        elif project.language.value == "C":
            if is_msvc:
                # MSVC C standards
                if "23" in project.cdialect or "2b" in project.cdialect:
                    flags.append("/std:c11")
                elif "17" in project.cdialect:
                    flags.append("/std:c17")
                elif "11" in project.cdialect:
                    flags.append("/std:c11")
                elif "99" in project.cdialect:
                    flags.append("/std:c99")
            else:
                # GCC/Clang C standards
                if "23" in project.cdialect or "2b" in project.cdialect:
                    flags.append("-std=c2x")
                elif "17" in project.cdialect:
                    flags.append("-std=c17")
                elif "11" in project.cdialect:
                    flags.append("-std=c11")
                elif "99" in project.cdialect:
                    flags.append("-std=c99")
                else:
                    flags.append("-std=c11")
        
        # Optimisation
        optimize = project.optimize
        for filter_expr, opt in project._filtered_optimize.items():
            if self._filter_matches(filter_expr, config, platform):
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
        
        # Debug symbols
        symbols = project.symbols
        for filter_expr, sym in project._filtered_symbols.items():
            if self._filter_matches(filter_expr, config, platform):
                symbols = sym
        
        if symbols:
            if is_msvc:
                flags.extend(["/Zi", "/FS"])
            else:
                flags.append("-g")
        
        # PIC pour bibliothèques partagées
        if project.kind == ProjectKind.SHARED_LIB and not is_msvc:
            flags.append("-fPIC")
        
        # Warnings
        warnings_level = project.warnings.lower()
        if warnings_level in ["all", "extra", "pedantic"]:
            if is_msvc:
                if warnings_level == "all":
                    flags.append("/W4")
                elif warnings_level == "extra":
                    flags.append("/W4")
                elif warnings_level == "pedantic":
                    flags.append("/W4")
            else:
                if warnings_level == "all":
                    flags.append("-Wall")
                elif warnings_level == "extra":
                    flags.append("-Wextra")
                elif warnings_level == "pedantic":
                    flags.append("-pedantic")
        
        # Flags spécifiques au compilateur
        if is_msvc:
            flags.extend([
                "/EHsc",       # Exception handling
                "/W3",         # Warning level 3 par défaut
                "/nologo",     # Pas de bannière
                "/permissive-", # Conformité stricte
            ])
            
            # Runtime library
            if config == "Debug":
                flags.append("/MDd")
            else:
                flags.append("/MD")
                
        elif is_clang:
            # Flags Clang spécifiques
            flags.extend([
                "-fcolor-diagnostics",
                "-fno-omit-frame-pointer",
            ])
            
        elif is_gcc:
            # Flags GCC spécifiques
            flags.extend([
                "-fdiagnostics-color=always",
            ])
        
        # Flags de la toolchain
        if project.language.value == "C++":
            flags.extend(toolchain.cxxflags)
        else:
            flags.extend(toolchain.cflags)
        
        return flags
    
    def _filter_matches(self, filter_expr: str, config: str, platform: str) -> bool:
        """Vérifie si un filtre correspond"""
        if ":" not in filter_expr:
            return False
        
        filter_type, filter_value = filter_expr.split(":", 1)
        
        if filter_type == "configurations":
            return filter_value == config
        elif filter_type == "system":
            return filter_value == platform
        
        return False
    
    def _build_compile_command(self, compiler: str, source_file: str, object_file: str,
                              includes: List[str], defines: List[str], flags: List[str]) -> List[str]:
        """Construit une commande de compilation"""
        
        is_msvc = "cl.exe" in compiler.lower() or "cl" == compiler.lower()
        
        cmd = [compiler]
        cmd.extend(flags)
        
        # Définitions
        for define in defines:
            if is_msvc:
                cmd.append(f"/D{define}")
            else:
                cmd.append(f"-D{define}")
        
        # Includes
        for inc_dir in includes:
            if is_msvc:
                cmd.append(f"/I{inc_dir}")
            else:
                cmd.append(f"-I{inc_dir}")
        
        # Source et sortie
        if is_msvc:
            cmd.extend(["/c", source_file, f"/Fo{object_file}"])
        else:
            cmd.extend(["-c", source_file, "-o", object_file])
        
        return cmd
    
    def _build_link_command(self, project: Project, toolchain: Toolchain, object_files: List[str],
                           output_file: str, lib_dirs: List[str], links: List[str],
                           expander: VariableExpander) -> GeneratedLinkCommand:
        """Construit une commande de linkage"""
        
        linker = toolchain.linker or toolchain.compiler
        is_msvc = "cl.exe" in linker.lower() or "link.exe" in linker.lower()
        
        cmd = []
        
        if project.kind == ProjectKind.STATIC_LIB:
            if is_msvc:
                cmd = ["lib.exe", "/nologo", f"/OUT:{output_file}"] + object_files
            else:
                cmd = [toolchain.archiver or "ar", "rcs", output_file] + object_files
        else:
            if is_msvc:
                cmd = ["link.exe", "/nologo"] + object_files + [f"/OUT:{output_file}"]
                
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
            else:
                cmd = [linker] + object_files + ["-o", output_file]
                
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
                
                if project.kind == ProjectKind.SHARED_LIB:
                    cmd.append("-shared")
        
        return GeneratedLinkCommand(
            output=output_file,
            objects=object_files,
            command=cmd,
            libraries=links,
            lib_dirs=lib_dirs
        )
    
    def _get_output_path(self, project: Project, target_dir: Path, 
                        expander: VariableExpander) -> str:
        """Chemin de sortie avec vérification du répertoire parent"""
        
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
        
        # Assurer que le répertoire parent existe
        output_path = target_dir / f"{target_name}{ext}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        return str(output_path)
    
    def _get_compiler(self, toolchain: Toolchain, is_cpp: bool) -> str:
        """Récupère le compilateur avec détection automatique"""
        
        # Priorité 1: Chemin explicite
        if is_cpp:
            if toolchain.cppcompiler_path:
                return toolchain.cppcompiler_path
            elif toolchain.cppcompiler:
                return toolchain.cppcompiler
        else:
            if toolchain.ccompiler_path:
                return toolchain.ccompiler_path
            elif toolchain.ccompiler:
                return toolchain.ccompiler
        
        # Priorité 2: Compilateur général
        if toolchain.compiler_path:
            return toolchain.compiler_path
        elif toolchain.compiler:
            return toolchain.compiler
        
        # Priorité 3: Détection automatique basée sur la plateforme
        import shutil
        
        if is_cpp:
            # Chercher C++ compiler
            for compiler in ["g++", "clang++", "c++", "cl", "cl.exe"]:
                if shutil.which(compiler):
                    return compiler
            
            # Dernier recours
            if self.platform == "Windows":
                return "cl.exe"
            else:
                return "g++"
        else:
            # Chercher C compiler
            for compiler in ["gcc", "clang", "cc", "cl", "cl.exe"]:
                if shutil.which(compiler):
                    return compiler
            
            # Dernier recours
            if self.platform == "Windows":
                return "cl.exe"
            else:
                return "gcc"