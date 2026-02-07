"""
Jenga Build System
A modern multi-platform C/C++ build system with unified Python DSL.
"""

__version__ = "1.1.0"
__author__ = "Rihen"
__email__ = "rihen.universe@gmail.com"

import importlib.util
import os
import sys
from pathlib import Path

# Déclarer explicitement les modules pour aider les outils d'analyse
__all__ = [
    'jenga',
    'Commands',
    'core',
    'utils',
]

# Fonction utilitaire pour charger les fichiers .jenga
def load_jenga_module(name: str, filepath: str):
    """Charge un module depuis un fichier .jenga"""
    spec = importlib.util.spec_from_file_location(name, filepath)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    return None

# Charger automatiquement les fichiers .jenga dans le package
_package_dir = Path(__file__).parent

# Chercher tous les fichiers .jenga et les exposer comme modules virtuels
for jenga_file in _package_dir.rglob("*.jenga"):
    if jenga_file.is_file():
        # Créer un nom de module basé sur le chemin
        rel_path = jenga_file.relative_to(_package_dir)
        module_name = f"Jenga.{rel_path.with_suffix('').as_posix().replace('/', '.')}"
        
        # Charger le module
        load_jenga_module(module_name, str(jenga_file))

# Alternative: Charger dynamiquement au moment de l'import
class JengaLoader:
    """Chargeur personnalisé pour les fichiers .jenga"""
    
    @staticmethod
    def find_spec(fullname, path, target=None):
        if fullname.startswith("Jenga."):
            # Convertir le nom de module en chemin de fichier
            module_path = fullname.replace("Jenga.", "").replace(".", "/")
            
            # Essayer plusieurs extensions
            possible_paths = [
                _package_dir / f"{module_path}.jenga",
                _package_dir / f"{module_path}.py",
                _package_dir / module_path / "__init__.jenga",
                _package_dir / module_path / "__init__.py",
            ]
            
            for filepath in possible_paths:
                if filepath.exists():
                    spec = importlib.util.spec_from_file_location(fullname, str(filepath))
                    return spec
        
        return None

# Ajouter le chargeur au système d'import
if JengaLoader not in sys.meta_path:
    sys.meta_path.insert(0, JengaLoader)

# Exporter les modules principaux pour faciliter les imports
try:
    # Essayer d'importer les modules principaux
    from . import Commands
    from . import core
    from . import utils
    
    __all__.extend(['Commands', 'core', 'utils'])
except ImportError:
    # Les imports échoueront pendant l'installation, c'est normal
    pass

# Fonctions utilitaires exposées
def version():
    """Retourne la version de Jenga"""
    return __version__

def author():
    """Retourne l'auteur de Jenga"""
    return __author__