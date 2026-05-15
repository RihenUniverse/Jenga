#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache – OBSOLETE: SQLite cache désactivé.

HISTORIQUE:
Le cache SQLite était utilisé pour:
  - Sérialiser le workspace complet (projets, toolchains)
  - Tracker les modifications de fichiers .jenga (mtime, hash)
  - Éviter le rechargement complet du workspace

PROBLÈME:
Le cache SQLite causait des bugs critiques avec les builds multi-ABI/multi-plateformes:
  - Ne détectait pas les changements de platform/arch
  - Empêchait la compilation de tous les ABIs Android (seulement le premier compilait)
  - Ajoutait de la complexité sans gain réel de performance

SOLUTION ACTUELLE:
Jenga utilise désormais uniquement le cache basé sur les timestamps de fichiers:
  - Builder._NeedsCompileSource() vérifie les mtimes des .cpp et headers
  - Génère des fichiers .d de dépendances (comme GCC/Clang standard)
  - Plus simple, plus robuste, compatible multi-plateforme

Cette classe est conservée pour compatibilité API mais toutes les méthodes sont des no-ops.
La suppression complète de ce fichier nécessitera de mettre à jour tous les imports dans:
  - Jenga/Commands/*.py (18 fichiers)
  - Jenga/Core/Daemon.py

Pour l'instant, les méthodes retournent des valeurs par défaut pour ne pas casser le code existant.
"""

import sqlite3
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any, Set, Tuple
import threading

from ..Utils import FileSystem, Colored


class Cache:
    """
    OBSOLETE: Cache SQLite désactivé.

    Cette classe est maintenant un no-op. Toutes les méthodes retournent immédiatement
    sans effectuer d'opérations sur la base de données.

    Le cache de compilation se fait uniquement via les timestamps de fichiers dans Builder.py.
    """

    _CACHE_ROOT = Path(".jenga") / "cache"
    _CACHE_VERSION = 2

    def __init__(self, workspaceRoot: Path, workspaceName: Optional[str] = None):
        """Initialise le cache (no-op - aucune base de données n'est créée)."""
        self.workspaceRoot = workspaceRoot.resolve() if isinstance(workspaceRoot, Path) else Path(workspaceRoot).resolve()
        self.workspaceName = workspaceName or self.workspaceRoot.name
        self.dbPath = self.workspaceRoot / self._CACHE_ROOT / f"{self.workspaceName}.db"
        self._connection = None
        self._lock = threading.RLock()

    def SaveWorkspace(self, workspace: Any, entryFile: Path, loader: Any) -> None:
        """
        OBSOLETE: Ne sauvegarde plus rien.

        Le cache SQLite est désactivé. Cette méthode ne fait rien.
        Le cache de compilation se fait uniquement via les timestamps de fichiers.
        """
        pass

    def LoadWorkspace(self, entryFile: Path, loader: Any) -> Optional[Any]:
        """
        OBSOLETE: Retourne toujours None pour forcer le rechargement.

        Le cache SQLite est désactivé. Le workspace est toujours rechargé depuis les .jenga files.
        Le cache de compilation se fait uniquement via les timestamps de fichiers (_NeedsCompileSource).
        """
        return None

    def UpdateIncremental(self, entryFile: Path, loader: Any, currentWorkspace: Any) -> bool:
        """
        OBSOLETE: Retourne toujours False.

        Le cache SQLite est désactivé. Pas de mise à jour incrémentale.
        """
        return False

    def Invalidate(self) -> None:
        """
        OBSOLETE: Ne fait rien.

        Il n'y a plus de base de données SQLite à invalider.
        Le cache timestamp dans Builder.py se régénère automatiquement.
        """
        pass

    def Close(self) -> None:
        """Ferme la connexion (no-op - pas de connexion créée)."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Close()
