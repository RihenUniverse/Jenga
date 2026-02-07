#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nken Build System - Variables Module
Handles variable expansion for %{variable} syntax
"""

import re
from typing import Dict, Any, Optional
from pathlib import Path


class VariableExpander:
    """Handles variable expansion in configuration strings"""
    
    # Regex pattern for %{variable} or %{project.property}
    VAR_PATTERN = re.compile(r'%\{([^}]+)\}')
    
    def __init__(self, workspace=None, project=None, config: str = "Debug", platform: str = "Windows"):
        self.workspace = workspace
        self.project = project
        self.config = config
        self.platform = platform
        self.custom_vars: Dict[str, str] = {}
        
    def add_variable(self, name: str, value: str):
        """Add a custom variable"""
        self.custom_vars[name] = value
    
    def expand(self, text: str) -> str:
        """Expand all variables in text"""
        if not text or not isinstance(text, str):
            return text
        
        def replace_var(match):
            var_expr = match.group(1)
            value = self._resolve_variable(var_expr)
            return str(value) if value is not None else match.group(0)
        
        # Keep expanding until no more variables found (handles nested variables)
        prev_text = ""
        while prev_text != text:
            prev_text = text
            text = self.VAR_PATTERN.sub(replace_var, text)
        
        return text
    
    def expand_list(self, items: list) -> list:
        """Expand variables in a list of strings"""
        return [self.expand(item) for item in items]
    
    def _resolve_variable(self, var_expr: str) -> Optional[str]:
        """Resolve a variable expression"""
        
        # Handle project.property syntax
        if '.' in var_expr:
            parts = var_expr.split('.', 1)
            obj_name = parts[0]
            prop_name = parts[1]
            
            # Workspace properties
            if obj_name == "wks" or obj_name == "workspace":
                return self._get_workspace_property(prop_name)
            
            # Current project properties
            elif obj_name == "prj" or obj_name == "project":
                return self._get_project_property(self.project, prop_name)
            
            # Configuration properties
            elif obj_name == "cfg" or obj_name == "config":
                return self._get_config_property(prop_name)
            
            # Other project properties (project_name.property)
            elif self.workspace and obj_name in self.workspace.projects:
                target_project = self.workspace.projects[obj_name]
                
                # Check if current project depends on this project
                if self.project and obj_name not in self.project.dependson:
                    # Allow access anyway but warn (for debugging)
                    pass
                
                return self._get_project_property(target_project, prop_name)
        
        # Simple variables
        else:
            # Built-in variables
            builtin = self._get_builtin_variable(var_expr)
            if builtin is not None:
                return builtin
            
            # Custom variables
            if var_expr in self.custom_vars:
                return self.custom_vars[var_expr]
        
        return None
    
    def _get_builtin_variable(self, name: str) -> Optional[str]:
        """Get built-in variable value"""
        
        builtin_vars = {
            "config": self.config,
            "configuration": self.config,
            "platform": self.platform,
            "system": self.platform,
        }
        
        return builtin_vars.get(name.lower())
    
    def _get_workspace_property(self, prop_name: str) -> Optional[str]:
        """Get workspace property"""
        if not self.workspace:
            return None
        
        prop_lower = prop_name.lower()
        
        if prop_lower == "name":
            return self.workspace.name
        elif prop_lower == "location":
            return self.workspace.location or "."
        elif prop_lower == "buildcfg":
            return self.config
        
        # Try to get attribute directly
        return getattr(self.workspace, prop_name, None)
    
    def _get_project_property(self, proj, prop_name: str) -> Optional[str]:
        """Get project property"""
        if not proj:
            return None
        
        prop_lower = prop_name.lower()
        
        if prop_lower == "name":
            return proj.name
        elif prop_lower == "location":
            return proj.location or "."
        elif prop_lower == "targetdir":
            return proj.targetdir
        elif prop_lower == "objdir":
            return proj.objdir
        elif prop_lower == "targetname":
            return proj.targetname or proj.name
        elif prop_lower == "kind":
            return proj.kind.value
        elif prop_lower == "language":
            return proj.language.value
        
        # Try to get attribute directly
        return getattr(proj, prop_name, None)
    
    def _get_config_property(self, prop_name: str) -> Optional[str]:
        """Get configuration property"""
        prop_lower = prop_name.lower()
        
        if prop_lower == "buildcfg":
            return self.config
        elif prop_lower == "platform":
            return self.platform
        elif prop_lower == "system":
            return self.platform
        elif prop_lower == "architecture":
            return "x64"  # Default, can be made configurable
        
        return None


def expand_path_patterns(pattern: str, base_dir: str = ".") -> list:
    """
    Expand path patterns with wildcards:
    - *.cpp: all .cpp files in directory
    - **.cpp: all .cpp files recursively
    - !file.cpp: exclude file
    """
    from pathlib import Path
    
    results = []
    exclude = False
    
    # Check for exclusion prefix
    if pattern.startswith("!"):
        exclude = True
        pattern = pattern[1:].strip()
    
    # Convert to Path
    pattern_path = Path(pattern)
    
    # Determine base path
    if pattern_path.is_absolute():
        base_path = Path("/")
        working_pattern = pattern
    else:
        base_path = Path(base_dir)
        working_pattern = pattern
    
    # Handle ** recursive patterns
    if "**" in working_pattern:
        # Split on **
        parts = working_pattern.split("**", 1)
        prefix = parts[0].rstrip("/\\")
        suffix = parts[1].lstrip("/\\") if len(parts) > 1 else ""
        
        # Determine search directory
        if prefix:
            if Path(prefix).is_absolute():
                search_dir = Path(prefix)
            else:
                prefix = prefix.lstrip("/\\")
                search_dir = base_path / prefix
        else:
            search_dir = base_path
        
        # Prepare glob pattern for suffix
        if suffix:
            # If suffix starts with . (like .cpp), add * before it
            if suffix.startswith(".") or (suffix and "*" not in suffix):
                glob_pattern = "*" + suffix if suffix.startswith(".") else suffix
            else:
                glob_pattern = suffix
        else:
            glob_pattern = "*"
        
        # Search recursively
        if search_dir.exists() and search_dir.is_dir():
            for file_path in search_dir.rglob(glob_pattern):
                if file_path.is_file():
                    results.append((str(file_path), exclude))
    
    # Handle * non-recursive patterns
    elif "*" in working_pattern:
        if Path(working_pattern).is_absolute():
            parent = Path(working_pattern).parent
            pattern_name = Path(working_pattern).name
            if parent.exists():
                for file_path in parent.glob(pattern_name):
                    if file_path.is_file():
                        results.append((str(file_path), exclude))
        else:
            parts = working_pattern.rsplit("/", 1)
            if len(parts) == 2:
                search_dir = base_path / parts[0]
                file_pattern = parts[1]
            else:
                search_dir = base_path
                file_pattern = working_pattern
            
            if search_dir.exists():
                for file_path in search_dir.glob(file_pattern):
                    if file_path.is_file():
                        results.append((str(file_path), exclude))
    
    # Handle exact file paths
    else:
        if Path(working_pattern).is_absolute():
            file_path = Path(working_pattern)
        else:
            file_path = base_path / remove_first_dir(working_pattern, True)

        if file_path.exists() and file_path.is_file():
            results.append((str(file_path), exclude))
    
    return results


def remove_first_dir(path: str, keep_empty: bool = False) -> str:
    """
    Retire le premier répertoire d'un chemin
    
    Args:
        path: Le chemin à transformer
        keep_empty: Si True, retourne "" si le chemin devient vide
    
    Exemples:
        "src/main.cpp" → "main.cpp"
        "include/utils/header.h" → "utils/header.h"
        "main.cpp" → "" (ou "main.cpp" si keep_empty=True)
        "C:\\src\\app.cpp" → "src\\app.cpp"
        "/usr/bin/app" → "usr/bin/app"
        "./src/app.cpp" → "src/app.cpp"
        "../src/app.cpp" → "src/app.cpp"
    """
    # Gérer les chemins vides
    if not path:
        return "" if keep_empty else path
    
    # Gérer les chemins commençant par ./ ou ../
    if path.startswith("./"):
        path = path[2:]
    elif path.startswith("../"):
        path = path[3:]  # On enlève le .. aussi
    
    # Utiliser pathlib pour une gestion propre
    p = Path(path)
    
    # Obtenir toutes les parties du chemin
    parts = list(p.parts)
    
    # Si on a une partie vide (pour les chemins Unix absolus comme "/usr/bin")
    if parts and parts[0] == "":
        parts = parts[1:]  # Retirer la partie vide
    
    # Si on a une lettre de lecteur (Windows: "C:")
    if len(parts) > 0 and re.match(r'^[A-Za-z]:$', parts[0]):
        parts = parts[1:]  # Retirer la lettre de lecteur
    
    # Maintenant retirer le premier répertoire valide
    if len(parts) > 1:
        result = Path(*parts[1:])
        return str(result)
    elif len(parts) == 1:
        # Un seul élément : c'est soit un fichier soit un répertoire terminal
        if keep_empty:
            return str(p)
        else:
            return ""  # Plus rien après retrait
    else:
        return ""


def resolve_file_list(patterns: list, base_dir: str = ".", expander: VariableExpander = None) -> list:
    """
    Resolve a list of file patterns into actual file paths
    Handles:
    - Variable expansion
    - Wildcard expansion (*, **)
    - Exclusions (!)
    """
    included_files = set()
    excluded_files = set()
    
    for pattern in patterns:
        # Expand variables first
        if expander:
            pattern = expander.expand(pattern)
        
        # Expand wildcards
        expanded = expand_path_patterns(pattern, base_dir)
        
        for file_path, is_exclude in expanded:
            if is_exclude:
                excluded_files.add(file_path)
            else:
                included_files.add(file_path)
    
    # Remove excluded files
    final_files = included_files - excluded_files
    
    return sorted(list(final_files))