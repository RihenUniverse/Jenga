"""
Chargeur personnalisé pour les fichiers .jenga
Permet d'importer des fichiers .jenga comme des modules Python
"""

import sys
import importlib.util
import importlib.abc
import os
from pathlib import Path

class JengaLoader(importlib.abc.Loader):
    """Chargeur pour les fichiers .jenga"""
    
    def __init__(self, fullname, path):
        self.fullname = fullname
        self.path = path
    
    def create_module(self, spec):
        """Crée un nouveau module"""
        return None  # Utilise le comportement par défaut
    
    def exec_module(self, module):
        """Exécute le module"""
        with open(self.path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Compiler et exécuter le code
        compiled = compile(code, self.path, 'exec')
        exec(compiled, module.__dict__)

class JengaFinder(importlib.abc.MetaPathFinder):
    """Chercheur pour les fichiers .jenga"""
    
    def find_spec(self, fullname, path, target=None):
        # Vérifier si c'est un module Jenga
        if fullname.startswith('Jenga.') or not path:
            return None
        
        # Chercher le fichier .jenga
        module_parts = fullname.split('.')
        module_name = module_parts[-1]
        
        for entry in path:
            if not isinstance(entry, str):
                continue
            
            # Chercher fichier .jenga
            jenga_path = os.path.join(entry, module_name + '.jenga')
            if os.path.exists(jenga_path):
                spec = importlib.util.spec_from_file_location(
                    fullname, 
                    jenga_path,
                    loader=JengaLoader(fullname, jenga_path)
                )
                return spec
            
            # Chercher dans un sous-dossier
            jenga_dir = os.path.join(entry, module_name)
            jenga_init = os.path.join(jenga_dir, '__init__.jenga')
            if os.path.exists(jenga_init):
                spec = importlib.util.spec_from_file_location(
                    fullname,
                    jenga_init,
                    loader=JengaLoader(fullname, jenga_init)
                )
                return spec
        
        return None

# Enregistrer le chercheur
sys.meta_path.insert(0, JengaFinder())

# Fonction utilitaire pour charger un fichier .jenga
def load_jenga_file(filepath, module_name=None):
    """
    Charge un fichier .jenga comme un module Python
    
    Args:
        filepath: Chemin vers le fichier .jenga
        module_name: Nom du module (optionnel)
    
    Returns:
        Le module chargé
    """
    if module_name is None:
        module_name = Path(filepath).stem
    
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    raise ImportError(f"Impossible de charger le fichier .jenga: {filepath}")