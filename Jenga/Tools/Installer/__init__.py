"""
Jenga Installer — système d'installateur self-extracting multi-plateforme.

Produit un exécutable d'installation autonome (stub C compilé + payload) sans
aucune dépendance externe. Voir DESIGN.md.

API principale : Builder.BuildInstaller(...).
"""
from .Builder import BuildInstaller, DetectCCompiler, BuilderError

__all__ = ["BuildInstaller", "DetectCCompiler", "BuilderError"]
