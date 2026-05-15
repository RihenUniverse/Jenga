#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State – État d'un build en cours.

Contient :
  - Projets déjà compilés / en échec
  - Hash des fichiers sources et headers (pour build incrémental)
  - Dépendances découvertes (par projet)
  - Fichiers objets produits

Peut être sérialisé/désérialisé pour reprise de build.
Toutes les méthodes publiques sont en PascalCase.
"""

import time
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

# ✅ Import absolu cohérent avec l'API utilisateur
from Jenga.Core import Api


@dataclass
class FileState:
    """État d'un fichier source : hash et timestamp."""
    hash: str
    mtime: float
    checked: float = field(default_factory=time.time)


class BuildState:
    """
    État mutable d'un build.
    Instance unique par exécution de commande.
    """

    def __init__(self, workspace: Any, platform: str = "", targetArch: str = ""):
        self.workspace = workspace
        self.workspaceName: str = getattr(workspace, 'name', 'unknown')
        self.platform = platform  # e.g., "android-arm64-v8a", "windows-x64-msvc"
        self.targetArch = targetArch  # e.g., "arm64", "x86_64"
        self.compiledProjects: Set[str] = set()
        self.failedProjects: Set[str] = set()
        self.startTime: float = time.time()
        self.endTime: Optional[float] = None

        # Mapping fichier -> état
        self._fileStates: Dict[str, FileState] = {}

        # Dépendances (headers) par projet
        self._projectDeps: Dict[str, Set[str]] = {}

        # Sorties (objets, libs, exécutables) par projet
        self._projectOutputs: Dict[str, List[str]] = {}

        # Flags de configuration (pour savoir si le projet doit être recompilé)
        self._configHash: Optional[str] = None

        # NEW: Track compiled projects per (project, platform, arch) context
        # Format: "ProjectName:platform:arch" → prevents ABI conflicts in multi-ABI builds
        self._compiledProjectsPerContext: Set[str] = set()
        self._failedProjectsPerContext: Set[str] = set()

    # -----------------------------------------------------------------------
    # Gestion des projets
    # -----------------------------------------------------------------------

    def _GetProjectKey(self, projectName: str, platform: Optional[str] = None, targetArch: Optional[str] = None) -> str:
        """
        Génère une clé unique pour un projet dans un contexte donné.

        Pour éviter les conflits dans les builds multi-ABI/multi-plateforme (ex: Android),
        chaque combinaison (project, platform, arch) est trackée séparément.

        Examples:
            - "NativeApp:android-arm64-v8a:arm64"
            - "NativeApp:android-x86_64:x86_64"
            - "MyApp:windows-x64-msvc:x86_64"
        """
        plat = platform if platform is not None else self.platform
        arch = targetArch if targetArch is not None else self.targetArch
        if plat or arch:
            return f"{projectName}:{plat}:{arch}"
        return projectName  # Fallback: pas de contexte

    def MarkProjectCompiled(self, projectName: str, success: bool = True,
                           platform: Optional[str] = None, targetArch: Optional[str] = None) -> None:
        """Marque un projet comme compilé (ou échoué) pour un contexte donné."""
        key = self._GetProjectKey(projectName, platform, targetArch)

        if success:
            # Legacy (for backward compat - some code may still check compiledProjects)
            self.compiledProjects.add(projectName)
            self.failedProjects.discard(projectName)

            # NEW: Context-aware tracking
            self._compiledProjectsPerContext.add(key)
            self._failedProjectsPerContext.discard(key)
        else:
            self.failedProjects.add(projectName)
            self._failedProjectsPerContext.add(key)

    def IsProjectCompiled(self, projectName: str, platform: Optional[str] = None, targetArch: Optional[str] = None) -> bool:
        """Vérifie si un projet a été compilé pour un contexte donné."""
        key = self._GetProjectKey(projectName, platform, targetArch)

        # If platform/arch context is specified → ONLY check context-aware tracking
        # (don't use legacy fallback, as it would incorrectly return True for different ABIs)
        if platform is not None or targetArch is not None:
            return key in self._compiledProjectsPerContext

        # No context specified → check both (for backward compatibility)
        return key in self._compiledProjectsPerContext or projectName in self.compiledProjects

    def HasProjectFailed(self, projectName: str, platform: Optional[str] = None, targetArch: Optional[str] = None) -> bool:
        """Vérifie si un projet a échoué pour un contexte donné."""
        key = self._GetProjectKey(projectName, platform, targetArch)
        if key in self._failedProjectsPerContext:
            return True
        return projectName in self.failedProjects

    def Reset(self) -> None:
        """Réinitialise l'état pour un nouveau build."""
        self.compiledProjects.clear()
        self.failedProjects.clear()
        self.startTime = time.time()
        self.endTime = None

    def Finish(self) -> None:
        self.endTime = time.time()

    @property
    def Elapsed(self) -> float:
        if self.endTime:
            return self.endTime - self.startTime
        return time.time() - self.startTime

    # -----------------------------------------------------------------------
    # Gestion des fichiers et hash
    # -----------------------------------------------------------------------

    def UpdateFileState(self, filepath: str, filehash: str, mtime: float) -> None:
        """Met à jour l'état d'un fichier."""
        self._fileStates[filepath] = FileState(hash=filehash, mtime=mtime)

    def GetFileState(self, filepath: str) -> Optional[FileState]:
        return self._fileStates.get(filepath)

    def GetFileHash(self, filepath: str) -> Optional[str]:
        state = self._fileStates.get(filepath)
        return state.hash if state else None

    def HasFileChanged(self, filepath: str, currentHash: str, currentMtime: float) -> bool:
        """Compare avec l'état enregistré."""
        state = self._fileStates.get(filepath)
        if state is None:
            return True  # jamais vu
        return state.hash != currentHash or state.mtime != currentMtime

    def RemoveFileState(self, filepath: str) -> None:
        """Supprime l'état d'un fichier (s'il a été effacé)."""
        self._fileStates.pop(filepath, None)

    # -----------------------------------------------------------------------
    # Gestion des dépendances
    # -----------------------------------------------------------------------

    def SetProjectDependencies(self, projectName: str, dependencies: Set[str]) -> None:
        """Enregistre l'ensemble des fichiers (headers) dont dépend un projet."""
        self._projectDeps[projectName] = set(dependencies)

    def GetProjectDependencies(self, projectName: str) -> Set[str]:
        return self._projectDeps.get(projectName, set())

    def AddProjectDependency(self, projectName: str, dependency: str) -> None:
        if projectName not in self._projectDeps:
            self._projectDeps[projectName] = set()
        self._projectDeps[projectName].add(dependency)

    # -----------------------------------------------------------------------
    # Gestion des sorties
    # -----------------------------------------------------------------------

    def AddProjectOutput(self, projectName: str, outputFile: str) -> None:
        if projectName not in self._projectOutputs:
            self._projectOutputs[projectName] = []
        self._projectOutputs[projectName].append(outputFile)

    def GetProjectOutputs(self, projectName: str) -> List[str]:
        return self._projectOutputs.get(projectName, [])

    def ClearProjectOutputs(self, projectName: str) -> None:
        self._projectOutputs.pop(projectName, None)

    # -----------------------------------------------------------------------
    # Sérialisation / désérialisation
    # -----------------------------------------------------------------------

    def ToDict(self) -> Dict[str, Any]:
        """Convertit l'état en dictionnaire sérialisable JSON."""
        return {
            'workspaceName': self.workspaceName,
            'compiledProjects': list(self.compiledProjects),
            'failedProjects': list(self.failedProjects),
            'startTime': self.startTime,
            'endTime': self.endTime,
            'fileStates': {k: asdict(v) for k, v in self._fileStates.items()},
            'projectDeps': {k: list(v) for k, v in self._projectDeps.items()},
            'projectOutputs': self._projectOutputs,
        }

    def Save(self, path: Path) -> None:
        """Sauvegarde l'état dans un fichier JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.ToDict(), f, indent=2)

    @classmethod
    def Load(cls, path: Path, workspace: Any) -> Optional['BuildState']:
        """Charge un état depuis un fichier JSON."""
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            state = cls(workspace)
            state.workspaceName = data.get('workspaceName', 'unknown')
            state.compiledProjects = set(data.get('compiledProjects', []))
            state.failedProjects = set(data.get('failedProjects', []))
            state.startTime = data.get('startTime', time.time())
            state.endTime = data.get('endTime')

            # Reconstruire les FileState
            for fp, fs in data.get('fileStates', {}).items():
                state._fileStates[fp] = FileState(**fs)

            # Dépendances
            for proj, deps in data.get('projectDeps', {}).items():
                state._projectDeps[proj] = set(deps)

            state._projectOutputs = data.get('projectOutputs', {})
            return state
        except Exception as e:
            print(f"Failed to load build state: {e}")
            return None