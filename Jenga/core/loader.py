#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Configuration Loader
Loads and executes .jenga files
"""

import sys
from pathlib import Path
import importlib.util
import re

import os
import json
import time
import hashlib
from typing import Optional, Dict, Any, List
from dataclasses import asdict
import pickle

# Fix imports to work from any context
try:
    from .api import get_current_workspace, reset_state, _current_project, _current_workspace
    from .variables import VariableExpander, resolve_file_list
except ImportError:
    from core.api import get_current_workspace, reset_state
    try:
        from core.api import _current_project, _current_workspace
    except ImportError:
        _current_project = None
        _current_workspace = None
    try:
        from core.variables import VariableExpander, resolve_file_list
    except ImportError:
        # Fallback minimal implementation
        class VariableExpander:
            def __init__(self, workspace, project, config, platform):
                self.workspace = workspace
                self.project = project
                self.config = config
                self.platform = platform
            
            def expand(self, text: str) -> str:
                return text.replace("%{wks.location}", self.workspace.location or ".")

try:
    from ..utils.display import Display
except ImportError:
    from utils.display import Display


class JengaCache:
    """Gestionnaire de cache pour les configurations .jenga"""
    
    def __init__(self, jenga_file: Path):
        """
        Initialise le système de cache
        
        Args:
            jenga_file: Chemin vers le fichier .jenga principal
        """
        self.jenga_file = jenga_file.resolve()
        self.cache_dir = self.jenga_file.parent / ".jenga_cache"
        self.cache_file = self.cache_dir / f"{self.jenga_file.stem}.cache.json"
        self.files_cache_file = self.cache_dir / f"{self.jenga_file.stem}.files.json"
        
        # Créer le répertoire de cache si nécessaire
        self.cache_dir.mkdir(exist_ok=True)
        
        # Version du cache (invalide le cache si format change)
        self.cache_version = "2.0"
        
        # Cache des patterns de fichiers
        self.files_cache: Dict[str, Dict[str, Any]] = {}
        self._load_files_cache()
    
    def _load_files_cache(self):
        """Charger le cache des fichiers"""
        if self.files_cache_file.exists():
            try:
                with open(self.files_cache_file, 'r', encoding='utf-8') as f:
                    self.files_cache = json.load(f)
            except:
                self.files_cache = {}
    
    def _save_files_cache(self):
        """Sauvegarder le cache des fichiers"""
        try:
            with open(self.files_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.files_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Failed to save files cache: {e}")
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculer un hash rapide pour un fichier (mtime + taille)"""
        try:
            path = Path(file_path)
            if not path.exists():
                return ""
            
            # Utiliser mtime et taille pour un hash rapide
            stat = path.stat()
            mtime = stat.st_mtime
            size = stat.st_size
            
            hasher = hashlib.md5()
            hasher.update(f"{mtime}:{size}:{file_path}".encode())
            return hasher.hexdigest()
        except:
            return ""
    
    def _resolve_patterns_with_cache(self, patterns: List[str], base_dir: str, 
                                   expander: VariableExpander, cache_key: str) -> List[str]:
        """
        Résoudre les patterns avec cache intelligent
        
        Args:
            patterns: Liste des patterns à résoudre
            base_dir: Répertoire de base pour la résolution
            expander: Expander pour les variables
            cache_key: Clé unique pour ce projet/contexte
        
        Returns:
            Liste des fichiers résolus
        """
        from pathlib import Path
        
        resolved_files = []
        
        for pattern in patterns:
            # Expander les variables dans le pattern
            expanded_pattern = expander.expand(pattern)
            
            # Créer une clé de cache pour ce pattern
            pattern_hash = hashlib.md5(f"{cache_key}:{expanded_pattern}".encode()).hexdigest()[:16]
            cache_entry_key = f"{pattern_hash}"
            
            # Vérifier si le pattern est dans le cache et encore valide
            if cache_entry_key in self.files_cache:
                cache_entry = self.files_cache[cache_entry_key]
                
                # Vérifier si le pattern a changé
                if cache_entry.get("pattern") == expanded_pattern:
                    # Vérifier si les fichiers existent toujours
                    cached_files = cache_entry.get("files", [])
                    all_files_exist = True
                    
                    for file_path in cached_files:
                        if not Path(file_path).exists():
                            all_files_exist = False
                            break
                    
                    if all_files_exist:
                        resolved_files.extend(cached_files)
                        continue
            
            # Si pas dans le cache ou invalide, résoudre normalement
            # Utiliser glob pour la résolution des patterns
            import glob
            
            # Convertir le pattern en chemin absolu
            if Path(expanded_pattern).is_absolute():
                search_pattern = expanded_pattern
            else:
                search_pattern = str(Path(base_dir) / expanded_pattern)
            
            # Résoudre avec glob
            try:
                matched_files = glob.glob(search_pattern, recursive=True)
                
                # Filtrer seulement les fichiers (pas les répertoires)
                matched_files = [f for f in matched_files if Path(f).is_file()]
                
                # Ajouter au cache
                self.files_cache[cache_entry_key] = {
                    "pattern": expanded_pattern,
                    "base_dir": base_dir,
                    "files": matched_files,
                    "timestamp": time.time()
                }
                
                resolved_files.extend(matched_files)
                
            except Exception as e:
                print(f"⚠️ Warning: Failed to resolve pattern {pattern}: {e}")
                # Fallback: utiliser le pattern tel quel
                if Path(expanded_pattern).exists():
                    resolved_files.append(expanded_pattern)
        
        # Sauvegarder le cache après chaque résolution
        self._save_files_cache()
        
        return list(set(resolved_files))  # Supprimer les doublons
    
    def needs_rebuild(self, workspace_hash: str = None) -> bool:
        """
        Vérifier si le cache doit être reconstruit
        
        Args:
            workspace_hash: Hash du workspace actuel (optionnel)
        
        Returns:
            True si le cache doit être reconstruit
        """
        # Pas de cache fichier → rebuild nécessaire
        if not self.cache_file.exists():
            return True
        
        # .jenga modifié plus récemment que le cache → rebuild
        jenga_mtime = self.jenga_file.stat().st_mtime
        cache_mtime = self.cache_file.stat().st_mtime
        
        if jenga_mtime > cache_mtime:
            return True
        
        try:
            # Charger le cache pour vérifier la version
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Vérifier la version du cache
            if cache_data.get("version") != self.cache_version:
                return True
            
            # Vérifier le hash du workspace (si fourni)
            if workspace_hash and cache_data.get("workspace_hash") != workspace_hash:
                return True
            
            return False
            
        except:
            return True
    
    def save_workspace(self, workspace, additional_info: Dict[str, Any] = None):
        """
        Sauvegarder un workspace dans le cache
        
        Args:
            workspace: Workspace à sauvegarder
            additional_info: Informations supplémentaires à sauvegarder
        """
        from .api import Workspace, Project, Toolchain
        
        # Calculer un hash pour le workspace
        workspace_hash = self._calculate_workspace_hash(workspace)
        
        # Préparer les données à sauvegarder
        cache_data = {
            "version": self.cache_version,
            "timestamp": time.time(),
            "jenga_file": str(self.jenga_file),
            "workspace_hash": workspace_hash,
            "workspace": {
                "name": workspace.name,
                "location": workspace.location,
                "configurations": workspace.configurations,
                "platforms": workspace.platforms,
                "startproject": workspace.startproject,
            },
            "projects": {},
            "toolchains": {},
            "additional_info": additional_info or {}
        }
        
        # Sauvegarder les projets (sans les fichiers résolus)
        for name, project in workspace.projects.items():
            cache_data["projects"][name] = self._serialize_project(project)
        
        # Sauvegarder les toolchains
        for name, toolchain in workspace.toolchains.items():
            cache_data["toolchains"][name] = self._serialize_toolchain(toolchain)
        
        # Sauvegarder le cache
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            # print(f"✅ Cache sauvegardé: {self.cache_file}")
        except Exception as e:
            print(f"⚠️ Warning: Failed to save cache: {e}")
    
    def load_workspace(self):
        """
        Charger un workspace depuis le cache
        
        Returns:
            Workspace chargé ou None
        """
        from .api import Workspace, Project, Toolchain, ProjectKind, Language, Optimization
        
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Vérifier la version
            if cache_data.get("version") != self.cache_version:
                return None
            
            # Créer le workspace
            ws_data = cache_data["workspace"]
            workspace = Workspace(
                name=ws_data["name"],
                location=ws_data.get("location", ""),
                configurations=ws_data.get("configurations", ["Debug", "Release"]),
                platforms=ws_data.get("platforms", ["Windows"]),
                startproject=ws_data.get("startproject", "")
            )
            
            # Restaurer les toolchains
            for name, tc_data in cache_data.get("toolchains", {}).items():
                toolchain = Toolchain(
                    name=name,
                    compiler=tc_data.get("compiler", "")
                )
                
                # Restaurer les attributs
                for key, value in tc_data.items():
                    if key != "name" and hasattr(toolchain, key):
                        setattr(toolchain, key, value)
                
                workspace.toolchains[name] = toolchain
            
            # Restaurer les projets
            for name, proj_data in cache_data.get("projects", {}).items():
                # Créer le projet
                project = Project(
                    name=name,
                    kind=ProjectKind(proj_data["kind"]) if proj_data.get("kind") else ProjectKind.CONSOLE_APP,
                    language=Language(proj_data["language"]) if proj_data.get("language") else Language.CPP,
                    location=proj_data.get("location", ".")
                )
                
                # Restaurer les attributs simples
                simple_attrs = [
                    'cppdialect', 'cdialect', 'pchheader', 'pchsource',
                    'objdir', 'targetdir', 'targetname', 'warnings',
                    'toolchain', '_explicit_toolchain', 'is_test',
                    'parent_project', 'testmainfile', 'testmaintemplate',
                    'androidapplicationid', 'androidversioncode', 
                    'androidversionname', 'androidminsdk', 'androidtargetsdk',
                    'androidsign', 'androidkeystore', 'androidkeystorepass',
                    'androidkeyalias', 'iosbundleid', 'iosversion', 'iosminsdk'
                ]
                
                for attr in simple_attrs:
                    if attr in proj_data:
                        setattr(project, attr, proj_data[attr])
                
                # Restaurer les listes
                list_attrs = [
                    'files', 'excludefiles', 'excludemainfiles',
                    'includedirs', 'libdirs', 'links', 'dependson',
                    'dependfiles', 'embedresources', 'defines',
                    'prebuildcommands', 'postbuildcommands',
                    'prelinkcommands', 'postlinkcommands',
                    'testoptions', 'testfiles'
                ]
                
                for attr in list_attrs:
                    if attr in proj_data:
                        setattr(project, attr, proj_data[attr])
                
                # Restaurer les dicts
                if 'system_defines' in proj_data:
                    project.system_defines = proj_data['system_defines']
                if 'system_links' in proj_data:
                    project.system_links = proj_data['system_links']
                if '_filtered_defines' in proj_data:
                    project._filtered_defines = proj_data['_filtered_defines']
                if '_filtered_optimize' in proj_data:
                    project._filtered_optimize = {
                        k: Optimization(v) for k, v in proj_data['_filtered_optimize'].items()
                    }
                if '_filtered_symbols' in proj_data:
                    project._filtered_symbols = proj_data['_filtered_symbols']
                
                # Restaurer l'optimization
                if 'optimize' in proj_data:
                    project.optimize = Optimization(proj_data['optimize'])
                
                # Restaurer symbols
                if 'symbols' in proj_data:
                    project.symbols = proj_data['symbols']
                
                # Ajouter au workspace
                workspace.projects[name] = project
            
            # print(f"✅ Cache chargé: {len(workspace.projects)} projets")
            return workspace
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to load cache: {e}")
            return None
    
    def _serialize_project(self, project) -> Dict[str, Any]:
        """Sérialiser un projet pour le cache"""
        # Exclure les attributs temporaires et les gros objets
        exclude_attrs = {
            '_current_filter', '_in_workspace', '_standalone',
            '_external', '_external_file', '_external_dir',
            '_original_location'
        }
        
        serialized = {}
        
        for attr_name in dir(project):
            # Ignorer les attributs privés spéciaux et méthodes
            if attr_name.startswith('__') or callable(getattr(project, attr_name)):
                continue
            
            # Ignorer les attributs exclus
            if attr_name in exclude_attrs:
                continue
            
            try:
                value = getattr(project, attr_name)
                
                # Gérer les types spéciaux
                if hasattr(value, 'value'):  # Enum
                    serialized[attr_name] = value.value
                elif isinstance(value, (str, int, float, bool, type(None))):
                    serialized[attr_name] = value
                elif isinstance(value, (list, tuple)):
                    serialized[attr_name] = list(value)
                elif isinstance(value, dict):
                    serialized[attr_name] = dict(value)
                # Ignorer les autres types (comme les objets complexes)
                
            except:
                pass
        
        return serialized
    
    def _serialize_toolchain(self, toolchain) -> Dict[str, Any]:
        """Sérialiser un toolchain pour le cache"""
        serialized = {}
        
        for attr_name in dir(toolchain):
            if attr_name.startswith('_') or callable(getattr(toolchain, attr_name)):
                continue
            
            try:
                value = getattr(toolchain, attr_name)
                
                if isinstance(value, (str, int, float, bool, type(None))):
                    serialized[attr_name] = value
                elif isinstance(value, (list, tuple)):
                    serialized[attr_name] = list(value)
                elif isinstance(value, dict):
                    serialized[attr_name] = dict(value)
                    
            except:
                pass
        
        return serialized
    
    def _calculate_workspace_hash(self, workspace) -> str:
        """Calculer un hash pour le workspace"""
        import hashlib
        
        hasher = hashlib.md5()
        
        # Inclure les métadonnées du workspace
        hasher.update(workspace.name.encode())
        hasher.update(workspace.location.encode())
        hasher.update(str(workspace.configurations).encode())
        hasher.update(str(workspace.platforms).encode())
        
        # Inclure les noms des projets et toolchains
        hasher.update(str(sorted(workspace.projects.keys())).encode())
        hasher.update(str(sorted(workspace.toolchains.keys())).encode())
        
        return hasher.hexdigest()
    
    def clear(self):
        """Effacer le cache"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            if self.files_cache_file.exists():
                self.files_cache_file.unlink()
            # print("✅ Cache effacé")
        except:
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir des statistiques sur le cache"""
        stats = {
            "cache_file_exists": self.cache_file.exists(),
            "files_cache_entries": len(self.files_cache),
            "cache_dir": str(self.cache_dir)
        }
        
        if self.cache_file.exists():
            stats["cache_size"] = self.cache_file.stat().st_size
            stats["cache_mtime"] = time.ctime(self.cache_file.stat().st_mtime)
        
        return stats


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