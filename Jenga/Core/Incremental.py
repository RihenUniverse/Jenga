#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Incremental – Décision de recompilation basée sur les hash et les dépendances.
Calcule les empreintes des fichiers sources, des flags de compilation,
et des dépendances (headers). Compare avec l'état précédent (BuildState)
pour déterminer si un projet ou un fichier doit être recompilé.

Toutes les méthodes publiques sont en PascalCase.
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Set, Optional, Any, Tuple
from functools import lru_cache

from ..Utils import FileSystem
from .Api import Project
from .State import BuildState

# ✅ Import absolu cohérent avec l'API utilisateur
from Jenga.Core import Api


class Incremental:
    """
    Moteur de décision pour les builds incrémentaux.
    Ne stocke pas d'état persistant – utilise BuildState pour cela.
    """

    # -----------------------------------------------------------------------
    # Hachage de contenu
    # -----------------------------------------------------------------------

    @staticmethod
    def ComputeFileHash(filepath: str, algorithm: str = "sha256") -> str:
        """
        Calcule le hash d'un fichier. Utilisé pour détecter les changements.
        Par défaut sha256, plus fiable que mtime seul.
        """
        return FileSystem.ComputeFileHash(filepath, algorithm)

    @staticmethod
    def ComputeStringHash(content: str, algorithm: str = "sha256") -> str:
        """Calcule le hash d'une chaîne (flags, defines, etc.)."""
        return FileSystem.ComputeStringHash(content, algorithm)

    @staticmethod
    def ComputeFlagsHash(project: Project, config: str, platform: str) -> str:
        """
        Calcule une empreinte des flags de compilation et de linkage
        qui peuvent influencer la sortie. Tout changement de flag doit
        invalider le binaire.
        """
        # Récupérer tous les paramètres pertinents
        flags_parts = [
            project.language.value if project.language else "",
            project.cppdialect,
            project.cdialect,
            str(project.optimize.value if hasattr(project.optimize, 'value') else project.optimize),
            str(project.symbols),
            str(project.warnings.value if hasattr(project.warnings, 'value') else project.warnings),
            str(sorted(project.defines)),
            str(sorted(project.includeDirs)),
            str(sorted(project.links)),
            str(sorted(project.libDirs)),
            str(sorted(getattr(project, 'cflags', []))),
            str(sorted(getattr(project, 'cxxflags', []))),
            str(sorted(getattr(project, 'ldflags', []))),
            config,
            platform,
        ]
        content = "|".join(flags_parts)
        return Incremental.ComputeStringHash(content)

    # -----------------------------------------------------------------------
    # Détection de changement par projet
    # -----------------------------------------------------------------------

    @staticmethod
    def NeedRebuild(project: Project,
                    state: BuildState,
                    config: str,
                    platform: str) -> bool:
        """
        Détermine si le projet doit être recompilé.
        Critères :
        1. Le projet n'a jamais été compilé (pas dans compiledProjects)
        2. Un fichier source a changé (hash différent)
        3. Un fichier d'en-tête inclus a changé (via dépendances enregistrées)
        4. Les flags de compilation ont changé
        """
        # Jamais compilé ?
        if not state.IsProjectCompiled(project.name):
            return True

        # Vérifier les flags
        current_flags_hash = Incremental.ComputeFlagsHash(project, config, platform)
        if state.GetProjectFlagsHash(project.name) != current_flags_hash:
            return True

        # Vérifier les fichiers sources
        for src in project.files:
            # Résoudre le chemin absolu
            src_path = Incremental._ResolvePath(src, project.location)
            if not src_path.exists():
                continue  # fichier manquant ? On le traitera plus tard
            current_hash = Incremental.ComputeFileHash(str(src_path))
            if state.HasFileChanged(str(src_path), current_hash, src_path.stat().st_mtime):
                return True

        # Vérifier les dépendances (headers) enregistrées
        deps = state.GetProjectDependencies(project.name)
        for dep in deps:
            dep_path = Path(dep)
            if not dep_path.exists():
                # Le fichier a été supprimé – doit recompiler
                return True
            current_hash = Incremental.ComputeFileHash(str(dep_path))
            if state.HasFileChanged(dep, current_hash, dep_path.stat().st_mtime):
                return True

        return False

    @staticmethod
    def NeedRecompileSource(source_file: str,
                            object_file: str,
                            state: BuildState,
                            project_location: str = None) -> bool:
        """
        Détermine si un fichier source particulier doit être recompilé.
        Utile pour les compilations incrémentales au niveau fichier.
        """
        src_path = Incremental._ResolvePath(source_file, project_location)
        if not src_path.exists():
            return False  # fichier supprimé ? Ne pas compiler

        obj_path = Path(object_file)
        if not obj_path.exists():
            return True  # fichier objet absent

        # Comparer timestamp : si source plus récente que objet
        src_mtime = src_path.stat().st_mtime
        obj_mtime = obj_path.stat().st_mtime
        if src_mtime > obj_mtime:
            return True

        # Vérifier hash si disponible dans l'état
        current_hash = Incremental.ComputeFileHash(str(src_path))
        if state.HasFileChanged(str(src_path), current_hash, src_mtime):
            return True

        return False

    @staticmethod
    def _ResolvePath(path: str, base: Optional[str]) -> Path:
        """Résout un chemin par rapport à une base."""
        p = Path(path)
        if p.is_absolute():
            return p
        if base:
            return Path(base) / p
        return p.resolve()

    # -----------------------------------------------------------------------
    # Gestion des dépendances (headers)
    # -----------------------------------------------------------------------

    @staticmethod
    def ParseDependencies(dep_file: str) -> Set[str]:
        """
        Parse un fichier .d (format Make) produit par GCC/Clang/MSVC.
        Extrait la liste des dépendances (headers) pour un fichier source.
        """
        deps = set()
        try:
            content = Path(dep_file).read_text(encoding='utf-8')
            # Format : target.o: dep1 dep2 \
            #           dep3
            lines = content.replace('\\\n', ' ').replace('\\\r\n', ' ').split('\n')
            for line in lines:
                if ':' in line:
                    _, rest = line.split(':', 1)
                    parts = rest.strip().split()
                    deps.update(p for p in parts if p)
        except Exception:
            pass
        return deps

    @staticmethod
    def UpdateDependencies(project: Project,
                           source_file: str,
                           dep_file: str,
                           state: BuildState) -> None:
        """
        Met à jour l'état avec les dépendances découvertes pour un fichier source.
        """
        deps = Incremental.ParseDependencies(dep_file)
        # Convertir en chemins absolus
        abs_deps = set()
        base = Path(project.location) if project.location else Path.cwd()
        for d in deps:
            p = Path(d)
            if not p.is_absolute():
                p = (base / p).resolve()
            else:
                p = p.resolve()
            abs_deps.add(str(p))
        state.AddProjectDependencies(project.name, source_file, abs_deps)

    # -----------------------------------------------------------------------
    # Nettoyage des sorties
    # -----------------------------------------------------------------------

    @staticmethod
    def CleanOutputs(project: Project, state: BuildState) -> None:
        """
        Supprime les fichiers objets et binaires associés à un projet,
        et met à jour l'état en conséquence.
        """
        outputs = state.GetProjectOutputs(project.name)
        for out in outputs:
            try:
                FileSystem.RemoveFile(out, ignoreErrors=True)
            except:
                pass
        state.ClearProjectOutputs(project.name)
        state.RemoveProjectFromCompiled(project.name)