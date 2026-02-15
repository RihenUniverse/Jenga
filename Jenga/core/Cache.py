#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache – Gestionnaire de cache persistant intelligent pour workspaces Jenga.

Utilise SQLite pour stocker :
  - Le workspace sérialisé (après expansion complète) – objet Workspace réel
  - Les métadonnées de tous les fichiers .jenga du workspace (mtime, hash)
  - L'association projet/toolchain → fichier source

Le nom de la base de données est dérivé du nom du workspace ou du répertoire racine.
Format : .jenga/cache/<workspace_name>_<hash_racine>.db

Fonctionnalités professionnelles :
  - Détection automatique des fichiers .jenga ajoutés, modifiés, supprimés
  - Rechargement partiel : seuls les fichiers modifiés sont réexécutés
  - Fusion des nouveaux projets/toolchains avec le workspace en cache
  - Sérialisation/désérialisation fidèle des objets Jenga (Workspace, Project, Toolchain, UnitestConfig)
  - Transactions SQLite ACID
  - Thread‑safe
  - Invalidation manuelle (--no-cache)
"""

import json
import sqlite3
import time
import hashlib
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any, Set, Tuple
from dataclasses import asdict, is_dataclass
import threading

from ..Utils import FileSystem, Colored
from .Loader import Loader
from .Variables import VariableExpander

# ✅ Import absolu cohérent avec l'API utilisateur
from Jenga.Core import Api


class Cache:
    """
    Cache SQLite pour un workspace donné.
    Thread‑safe (connexions locales).
    """

    _CACHE_ROOT = Path(".jenga") / "cache"
    _CACHE_VERSION = 2  # Incrémenter en cas de changement de format

    def __init__(self, workspaceRoot: Path, workspaceName: Optional[str] = None):
        """
        workspaceRoot : répertoire racine du workspace (celui contenant le .jenga principal)
        workspaceName : nom du workspace (optionnel, utilisé pour nommer la DB)
        """
        self.workspaceRoot = workspaceRoot.resolve()
        self.workspaceName = workspaceName or self._DeriveWorkspaceName()
        self.dbPath = self._GetDatabasePath()
        self._connection = None
        self._lock = threading.RLock()
        self._EnsureDirectory()

    # -----------------------------------------------------------------------
    # Private helpers – _PascalCase
    # -----------------------------------------------------------------------

    def _DeriveWorkspaceName(self) -> str:
        """Génère un nom de workspace à partir du répertoire racine."""
        name = self.workspaceRoot.name
        # Nettoyage pour nom de fichier
        name = "".join(c for c in name if c.isalnum() or c in "._- ")
        name = name.strip().replace(' ', '_')
        if not name:
            name = "workspace"
        # Ajouter un hash du chemin complet pour éviter les collisions
        path_hash = hashlib.md5(str(self.workspaceRoot).encode()).hexdigest()[:8]
        return f"{name}_{path_hash}"

    def _GetDatabasePath(self) -> Path:
        """Détermine le chemin complet de la base SQLite."""
        db_filename = f"{self.workspaceName}.db"
        return self.workspaceRoot / self._CACHE_ROOT / db_filename

    def _EnsureDirectory(self) -> None:
        """Crée le répertoire de cache; fallback si non inscriptible."""
        try:
            self.dbPath.parent.mkdir(parents=True, exist_ok=True)
            return
        except Exception:
            pass

        root_hash = hashlib.md5(str(self.workspaceRoot).encode()).hexdigest()[:8]
        fallback_roots = [
            Path(__file__).resolve().parents[2] / ".jenga" / "cache",
            Path.home() / ".jenga" / "cache",
            Path(tempfile.gettempdir()) / "Jenga-cache",
        ]
        for root in fallback_roots:
            try:
                root.mkdir(parents=True, exist_ok=True)
                self.dbPath = root / f"{self.workspaceName}_{root_hash}.db"
                return
            except Exception:
                continue

        raise PermissionError(f"Cannot create cache directory for workspace: {self.workspaceRoot}")

    def _GetConnection(self) -> sqlite3.Connection:
        """Retourne une connexion SQLite thread‑safe."""
        with self._lock:
            if self._connection is None:
                self._connection = sqlite3.connect(
                    str(self.dbPath),
                    timeout=10.0,
                    check_same_thread=False,
                    isolation_level='DEFERRED'   # ← désactive l'autocommit, transactions manuelles
                )
                self._connection.row_factory = sqlite3.Row
                self._connection.execute("PRAGMA foreign_keys = ON")
                self._connection.execute("PRAGMA journal_mode = WAL")
                self._connection.execute("PRAGMA synchronous = NORMAL")
                self._connection.execute("PRAGMA cache_size = -2000")
            return self._connection

    def _InitializeDatabase(self) -> None:
        """Crée les tables si elles n'existent pas."""
        conn = self._GetConnection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS workspace (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                mtime REAL NOT NULL,
                hash TEXT NOT NULL,
                last_loaded REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
                name TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                project_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS toolchains (
                name TEXT PRIMARY KEY,
                source_file TEXT NOT NULL,
                toolchain_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS metadata (
                version INTEGER PRIMARY KEY,
                workspace_root TEXT NOT NULL,
                workspace_name TEXT NOT NULL,
                cache_version INTEGER NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
        """)
        conn.commit()

    def _ComputeFileHash(self, filepath: Path) -> str:
        """Calcule le hash SHA‑256 d'un fichier."""
        return FileSystem.ComputeFileHash(str(filepath), algorithm="sha256")

    def _GetFileMetadata(self, filepath: Path) -> Tuple[float, str]:
        """Retourne (mtime, hash) du fichier."""
        mtime = FileSystem.GetModificationTime(str(filepath))
        filehash = self._ComputeFileHash(filepath)
        return mtime, filehash

    def _GetAllJengaFiles(self) -> Set[Path]:
        """Retourne tous les fichiers .jenga sous workspaceRoot."""
        files = set()
        for p in self.workspaceRoot.rglob("*.jenga"):
            # Ignorer les réperoires cachés (comme .jenga, .git, etc.)
            if any(part.startswith('.') for part in p.relative_to(self.workspaceRoot).parts):
                continue
            files.add(p.resolve())
        return files

    # -----------------------------------------------------------------------
    # Sérialisation / Désérialisation avancée
    # -----------------------------------------------------------------------

    @staticmethod
    def _EncodeEnum(obj):
        """Convertit une énumération en sa valeur."""
        return obj.value if hasattr(obj, 'value') else obj

    @staticmethod
    def _DecodeEnum(enumType, rawValue, default=None):
        """
        Convertit une valeur sérialisée en enum.
        Accepte:
        - l'instance enum déjà décodée
        - le nom du membre (ex: WINDOWS)
        - la valeur du membre (ex: Windows)
        """
        if rawValue is None:
            return default

        if isinstance(rawValue, enumType):
            return rawValue

        if isinstance(rawValue, str):
            # 1) Nom exact du membre
            if rawValue in enumType.__members__:
                return enumType[rawValue]

            # 2) Valeur ou nom (tolérance casse)
            lowered = rawValue.strip().lower()
            for member in enumType:
                if member.name.lower() == lowered:
                    return member
                if str(member.value).lower() == lowered:
                    return member

        return default

    @staticmethod
    def _DecodeEnumList(enumType, values: Any) -> List[Any]:
        result = []
        if not values:
            return result
        for raw in values:
            decoded = Cache._DecodeEnum(enumType, raw)
            if decoded is not None:
                result.append(decoded)
        return result

    @staticmethod
    def _ProjectFromDict(dct: Dict) -> Any:
        from .Api import Project, ProjectKind, Language, Optimization, WarningLevel
        from .Api import TargetOS, TargetArch, TargetEnv

        proj = Project(name=dct.get('name', ''))

        # Copier les champs simples présents dans le cache.
        for key, value in dct.items():
            if key == '__jenga_type__':
                continue
            if hasattr(proj, key):
                setattr(proj, key, value)

        # Reconversion explicite des enums.
        proj.kind = Cache._DecodeEnum(ProjectKind, dct.get('kind'), ProjectKind.CONSOLE_APP)
        proj.language = Cache._DecodeEnum(Language, dct.get('language'), Language.CPP)
        proj.optimize = Cache._DecodeEnum(Optimization, dct.get('optimize'), Optimization.OFF)
        proj.warnings = Cache._DecodeEnum(WarningLevel, dct.get('warnings'), WarningLevel.DEFAULT)
        proj.targetOs = Cache._DecodeEnum(TargetOS, dct.get('targetOs'))
        proj.targetArch = Cache._DecodeEnum(TargetArch, dct.get('targetArch'))
        proj.targetEnv = Cache._DecodeEnum(TargetEnv, dct.get('targetEnv'))

        return proj

    @staticmethod
    def _ToolchainFromDict(dct: Dict) -> Any:
        from .Api import Toolchain, CompilerFamily, TargetOS, TargetArch, TargetEnv

        compiler_family = Cache._DecodeEnum(
            CompilerFamily,
            dct.get('compilerFamily'),
            CompilerFamily.GCC
        )
        tc = Toolchain(name=dct.get('name', ''), compilerFamily=compiler_family)

        for key, value in dct.items():
            if key == '__jenga_type__':
                continue
            if hasattr(tc, key):
                setattr(tc, key, value)

        tc.compilerFamily = compiler_family
        tc.targetOs = Cache._DecodeEnum(TargetOS, dct.get('targetOs'))
        tc.targetArch = Cache._DecodeEnum(TargetArch, dct.get('targetArch'))
        tc.targetEnv = Cache._DecodeEnum(TargetEnv, dct.get('targetEnv'))

        return tc

    @staticmethod
    def _UnitestConfigFromDict(dct: Dict) -> Any:
        from .Api import UnitestConfig, ProjectKind

        ucfg = UnitestConfig()
        for key, value in dct.items():
            if key == '__jenga_type__':
                continue
            if hasattr(ucfg, key):
                setattr(ucfg, key, value)

        ucfg.kind = Cache._DecodeEnum(ProjectKind, dct.get('kind'), ProjectKind.STATIC_LIB)
        return ucfg

    @staticmethod
    def _JengaObjectHook(dct: Dict) -> Any:
        jenga_type = dct.get('__jenga_type__')
        if not jenga_type:
            return dct

        from .Api import Workspace, Project, Toolchain, UnitestConfig
        from .Api import TargetOS, TargetArch

        if jenga_type == 'Workspace':
            wks = Workspace(name=dct.get('name', ''))

            # Copier les champs simples.
            for key, value in dct.items():
                if key in ('__jenga_type__', 'projects', 'toolchains', 'unitestConfig', 'targetOses', 'targetArchs'):
                    continue
                if hasattr(wks, key):
                    setattr(wks, key, value)

            # Reconversion enum robuste.
            wks.targetOses = Cache._DecodeEnumList(TargetOS, dct.get('targetOses', []))
            wks.targetArchs = Cache._DecodeEnumList(TargetArch, dct.get('targetArchs', []))

            # IMPORTANT: restaurer les projets et toolchains du cache.
            restored_projects = {}
            for proj_name, raw_proj in (dct.get('projects', {}) or {}).items():
                if isinstance(raw_proj, Project):
                    restored_projects[proj_name] = raw_proj
                elif isinstance(raw_proj, dict):
                    restored_projects[proj_name] = Cache._ProjectFromDict(raw_proj)
            wks.projects = restored_projects

            restored_toolchains = {}
            for tc_name, raw_tc in (dct.get('toolchains', {}) or {}).items():
                if isinstance(raw_tc, Toolchain):
                    restored_toolchains[tc_name] = raw_tc
                elif isinstance(raw_tc, dict):
                    restored_toolchains[tc_name] = Cache._ToolchainFromDict(raw_tc)
            wks.toolchains = restored_toolchains

            raw_unitest = dct.get('unitestConfig')
            if isinstance(raw_unitest, UnitestConfig):
                wks.unitestConfig = raw_unitest
            elif isinstance(raw_unitest, dict):
                wks.unitestConfig = Cache._UnitestConfigFromDict(raw_unitest)

            return wks

        elif jenga_type == 'Project':
            return Cache._ProjectFromDict(dct)

        elif jenga_type == 'Toolchain':
            return Cache._ToolchainFromDict(dct)

        elif jenga_type == 'UnitestConfig':
            return Cache._UnitestConfigFromDict(dct)

        return dct

    def _SerializeWorkspace(self, workspace: Any) -> str:
        """
        Convertit un Workspace (et ses composants) en JSON.
        Ajoute des marqueurs de type pour la désérialisation.
        """
        from .Api import Workspace, Project, Toolchain, UnitestConfig
        from enum import Enum

        def default_serializer(obj):
            if isinstance(obj, Enum):
                return obj.value
            if is_dataclass(obj):
                d = asdict(obj)
                d['__jenga_type__'] = obj.__class__.__name__
                for k, v in d.items():
                    if isinstance(v, Enum):
                        d[k] = v.value
                return d
            if isinstance(obj, Workspace):
                d = obj.__dict__.copy()
                d = {k: v for k, v in d.items() if not k.startswith('_')}
                d['__jenga_type__'] = 'Workspace'
                d['targetOses'] = [self._EncodeEnum(e) for e in d.get('targetOses', [])]
                d['targetArchs'] = [self._EncodeEnum(e) for e in d.get('targetArchs', [])]
                # ✅ NE PAS VIDER projects ET toolchains
                # d['projects'] = {}
                # d['toolchains'] = {}
                return d
            if isinstance(obj, Project):
                d = obj.__dict__.copy()
                d = {k: v for k, v in d.items() if not k.startswith('_')}
                d['__jenga_type__'] = 'Project'
                for field in ['kind', 'language', 'optimize', 'warnings', 'targetOs', 'targetArch', 'targetEnv']:
                    if d.get(field) is not None:
                        val = d[field]
                        if isinstance(val, Enum):
                            d[field] = val.value
                return d
            if isinstance(obj, Toolchain):
                d = obj.__dict__.copy()
                d = {k: v for k, v in d.items() if not k.startswith('_')}
                d['__jenga_type__'] = 'Toolchain'
                for field in ['compilerFamily', 'targetOs', 'targetArch', 'targetEnv']:
                    if d.get(field) is not None:
                        val = d[field]
                        if isinstance(val, Enum):
                            d[field] = val.value
                return d
            if isinstance(obj, UnitestConfig):
                d = obj.__dict__.copy()
                d['__jenga_type__'] = 'UnitestConfig'
                if d.get('kind') is not None:
                    val = d['kind']
                    if isinstance(val, Enum):
                        d['kind'] = val.value
                return d
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(workspace, default=default_serializer, indent=2)

    def _DeserializeWorkspace(self, data: str) -> Any:
        """Reconstruit un Workspace depuis JSON."""
        obj = json.loads(data, object_hook=self._JengaObjectHook)
        return obj

    # -----------------------------------------------------------------------
    # Fusion incrémentale
    # -----------------------------------------------------------------------

    def _LoadExternalFileAndMerge(self,
                                  filepath: Path,
                                  currentWorkspace: Any,
                                  loader: Loader) -> Tuple[bool, List[str], List[str]]:
        """
        Recharge un fichier .jenga externe et fusionne son contenu dans le workspace courant.
        Retourne (succès, liste des projets ajoutés/mis à jour, liste des toolchains ajoutées).
        """
        try:
            tempWks, meta = loader.LoadExternalFile(str(filepath), currentWorkspace)
        except Exception as e:
            Colored.PrintError(f"Failed to reload {filepath}: {e}")
            return False, [], []

        # Fusion des projets
        updated_projects = []
        for name, proj in tempWks.projects.items():
            if name.startswith('__'):
                continue
            proj._external = True
            proj._externalFile = str(filepath)
            proj._externalDir = str(filepath.parent)
            expander = loader.GetExpanderForWorkspace(currentWorkspace)
            expander.SetWorkspace(currentWorkspace)
            expander.SetBaseDir(filepath.parent)
            expander.ExpandAll(proj, recursive=True)
            currentWorkspace.projects[name] = proj
            updated_projects.append(name)

        # Fusion des toolchains
        updated_toolchains = []
        for name, tc in tempWks.toolchains.items():
            if name not in currentWorkspace.toolchains:
                tc._external = True
                tc._externalFile = str(filepath)
                currentWorkspace.toolchains[name] = tc
                updated_toolchains.append(name)

        return True, updated_projects, updated_toolchains

    def _RemoveProjectsAndToolchainsFromFile(self, conn: sqlite3.Connection, filepath: str, workspace: Any) -> None:
        """Supprime les projets et toolchains associés à un fichier supprimé."""
        projs = conn.execute("SELECT name FROM projects WHERE source_file=?", (filepath,)).fetchall()
        for row in projs:
            proj_name = row['name']
            if proj_name in workspace.projects:
                del workspace.projects[proj_name]
            conn.execute("DELETE FROM projects WHERE name=?", (proj_name,))
        tcs = conn.execute("SELECT name FROM toolchains WHERE source_file=?", (filepath,)).fetchall()
        for row in tcs:
            tc_name = row['name']
            if tc_name in workspace.toolchains:
                del workspace.toolchains[tc_name]
            conn.execute("DELETE FROM toolchains WHERE name=?", (tc_name,))
        conn.execute("DELETE FROM files WHERE path=?", (filepath,))

    # -----------------------------------------------------------------------
    # Public API – PascalCase
    # -----------------------------------------------------------------------

    def SaveWorkspace(self, workspace: Any, entryFile: Path, loader: Loader) -> None:
        """
        Sauvegarde le workspace complet et les métadonnées des fichiers.
        Doit être appelée après un chargement complet réussi.
        """
        conn = self._GetConnection()
        self._InitializeDatabase()
        now = time.time()

        # Transaction implicite (isolation_level='DEFERRED'), on commit explicitement
        try:
            # Sérialiser le workspace
            workspace_json = self._SerializeWorkspace(workspace)
            conn.execute(
                "INSERT OR REPLACE INTO workspace (key, value, updated_at) VALUES (?, ?, ?)",
                ("workspace", workspace_json, now)
            )

            # Sauvegarder tous les fichiers .jenga du workspace
            all_files = self._GetAllJengaFiles()
            for fp in all_files:
                try:
                    mtime, fhash = self._GetFileMetadata(fp)
                    conn.execute(
                        "INSERT OR REPLACE INTO files (path, mtime, hash, last_loaded) VALUES (?, ?, ?, ?)",
                        (str(fp), mtime, fhash, now)
                    )
                except FileNotFoundError:
                    pass

            # Projets
            for proj_name, proj in workspace.projects.items():
                if proj_name.startswith('__'):
                    continue
                source_file = getattr(proj, '_externalFile', str(entryFile))
                proj_json = json.dumps({
                    'name': proj.name,
                    'kind': proj.kind.value if proj.kind else '',
                    'location': proj.location,
                    'external': getattr(proj, '_external', False),
                })
                conn.execute(
                    "INSERT OR REPLACE INTO projects (name, source_file, project_json, updated_at) VALUES (?, ?, ?, ?)",
                    (proj_name, source_file, proj_json, now)
                )

            # Toolchains
            for tc_name, tc in workspace.toolchains.items():
                source_file = getattr(tc, '_externalFile', str(entryFile))
                tc_json = json.dumps({
                    'name': tc.name,
                    'compilerFamily': tc.compilerFamily.value if tc.compilerFamily else '',
                    'targetOs': tc.targetOs.value if tc.targetOs else '',
                    'targetArch': tc.targetArch.value if tc.targetArch else '',
                    'external': getattr(tc, '_external', False),
                })
                conn.execute(
                    "INSERT OR REPLACE INTO toolchains (name, source_file, toolchain_json, updated_at) VALUES (?, ?, ?, ?)",
                    (tc_name, source_file, tc_json, now)
                )

            # Métadonnées
            conn.execute("""
                INSERT OR REPLACE INTO metadata (version, workspace_root, workspace_name, cache_version, created_at, updated_at)
                VALUES (1, ?, ?, ?,
                    COALESCE((SELECT created_at FROM metadata WHERE version=1), ?),
                    ?)
            """, (str(self.workspaceRoot), self.workspaceName, self._CACHE_VERSION, now, now))

            conn.commit()
            Colored.PrintInfo(f"Workspace cached to {self.dbPath}")
        except Exception:
            conn.rollback()
            raise

    def LoadWorkspace(self, entryFile: Path, loader: Loader) -> Optional[Any]:
        """
        Charge le workspace depuis le cache s'il est valide.
        Si des fichiers .jenga ont été modifiés/ajoutés/supprimés,
        recharge uniquement les fichiers affectés et fusionne les modifications.
        Retourne le workspace à jour (objet Workspace) ou None si le cache est absent/invalide.
        """
        conn = self._GetConnection()
        self._InitializeDatabase()

        row = conn.execute("SELECT value FROM workspace WHERE key='workspace'").fetchone()
        if not row:
            return None

        meta = conn.execute("SELECT cache_version FROM metadata WHERE version=1").fetchone()
        if not meta or meta['cache_version'] != self._CACHE_VERSION:
            Colored.PrintInfo("Cache format changed, reloading...")
            return None

        try:
            workspace = self._DeserializeWorkspace(row['value'])
            if workspace is None or not hasattr(workspace, 'projects'):
                return None
            # ✅ Le workspace contient déjà tous les projets et toolchains
        except Exception as e:
            Colored.PrintWarning(f"Cache deserialization failed: {e}, will reload")
            return None

        cached_files = conn.execute("SELECT path, mtime, hash FROM files").fetchall()
        cached_files_dict = {row['path']: (row['mtime'], row['hash']) for row in cached_files}

        current_files = self._GetAllJengaFiles()
        current_files_set = {str(p) for p in current_files}

        added = [p for p in current_files_set if p not in cached_files_dict]
        deleted = [p for p in cached_files_dict if p not in current_files_set]
        modified = []
        for p_str in current_files_set:
            if p_str in cached_files_dict:
                old_mtime, old_hash = cached_files_dict[p_str]
                try:
                    new_mtime, new_hash = self._GetFileMetadata(Path(p_str))
                    if new_mtime != old_mtime or new_hash != old_hash:
                        modified.append(p_str)
                except FileNotFoundError:
                    deleted.append(p_str)

        if not added and not deleted and not modified:
            # Message will be shown by BuildCoordinator
            workspace._cache_status = "no_changes"
            return workspace

        # Message will be shown if verbose
        workspace._cache_status = f"updated: {len(added)} added, {len(deleted)} deleted, {len(modified)} modified"

        now = time.time()
        try:
            # 1. Supprimer les fichiers disparus
            for p_str in deleted:
                self._RemoveProjectsAndToolchainsFromFile(conn, p_str, workspace)

            # 2. Recharger les fichiers modifiés
            for p_str in modified:
                fp = Path(p_str)
                success, updated_projs, updated_tcs = self._LoadExternalFileAndMerge(fp, workspace, loader)
                if success:
                    mtime, fhash = self._GetFileMetadata(fp)
                    conn.execute(
                        "INSERT OR REPLACE INTO files (path, mtime, hash, last_loaded) VALUES (?, ?, ?, ?)",
                        (p_str, mtime, fhash, now)
                    )
                    for proj_name in updated_projs:
                        proj = workspace.projects[proj_name]
                        proj_json = json.dumps({
                            'name': proj.name,
                            'kind': proj.kind.value if proj.kind else '',
                            'location': proj.location,
                            'external': True,
                        })
                        conn.execute(
                            "INSERT OR REPLACE INTO projects (name, source_file, project_json, updated_at) VALUES (?, ?, ?, ?)",
                            (proj_name, p_str, proj_json, now)
                        )
                    for tc_name in updated_tcs:
                        tc = workspace.toolchains[tc_name]
                        tc_json = json.dumps({
                            'name': tc.name,
                            'compilerFamily': tc.compilerFamily.value if tc.compilerFamily else '',
                            'external': True,
                        })
                        conn.execute(
                            "INSERT OR REPLACE INTO toolchains (name, source_file, toolchain_json, updated_at) VALUES (?, ?, ?, ?)",
                            (tc_name, p_str, tc_json, now)
                        )
                else:
                    Colored.PrintError(f"Failed to reload {p_str}")

            # 3. Ajouter les nouveaux fichiers
            for p_str in added:
                fp = Path(p_str)
                success, updated_projs, updated_tcs = self._LoadExternalFileAndMerge(fp, workspace, loader)
                if success:
                    mtime, fhash = self._GetFileMetadata(fp)
                    conn.execute(
                        "INSERT OR REPLACE INTO files (path, mtime, hash, last_loaded) VALUES (?, ?, ?, ?)",
                        (p_str, mtime, fhash, now)
                    )
                    for proj_name in updated_projs:
                        proj = workspace.projects[proj_name]
                        proj_json = json.dumps({
                            'name': proj.name,
                            'kind': proj.kind.value if proj.kind else '',
                            'location': proj.location,
                            'external': True,
                        })
                        conn.execute(
                            "INSERT OR REPLACE INTO projects (name, source_file, project_json, updated_at) VALUES (?, ?, ?, ?)",
                            (proj_name, p_str, proj_json, now)
                        )
                    for tc_name in updated_tcs:
                        tc = workspace.toolchains[tc_name]
                        tc_json = json.dumps({
                            'name': tc.name,
                            'compilerFamily': tc.compilerFamily.value if tc.compilerFamily else '',
                            'external': True,
                        })
                        conn.execute(
                            "INSERT OR REPLACE INTO toolchains (name, source_file, toolchain_json, updated_at) VALUES (?, ?, ?, ?)",
                            (tc_name, p_str, tc_json, now)
                        )
                else:
                    Colored.PrintError(f"Failed to load new file {p_str}")

            # 4. Mettre à jour le workspace sérialisé
            workspace_json = self._SerializeWorkspace(workspace)
            conn.execute(
                "INSERT OR REPLACE INTO workspace (key, value, updated_at) VALUES (?, ?, ?)",
                ("workspace", workspace_json, now)
            )
            conn.execute(
                "UPDATE metadata SET updated_at=? WHERE version=1",
                (now,)
            )
            conn.commit()
            Colored.PrintInfo("Workspace cache updated incrementally.")
        except Exception as e:
            conn.rollback()
            Colored.PrintError(f"Incremental update failed: {e}, will fallback to full reload")
            return None

        return workspace

    def UpdateIncremental(self, entryFile: Path, loader: Loader, currentWorkspace: Any) -> bool:
        """
        Met à jour le cache de manière incrémentale sans recharger le workspace depuis le cache.
        Utile pour le mode watch.
        Retourne True si le workspace a été modifié.
        """
        conn = self._GetConnection()
        self._InitializeDatabase()
        now = time.time()

        cached_files = conn.execute("SELECT path, mtime, hash FROM files").fetchall()
        cached_dict = {row['path']: (row['mtime'], row['hash']) for row in cached_files}

        current_files = self._GetAllJengaFiles()
        current_set = {str(p) for p in current_files}

        added = [p for p in current_set if p not in cached_dict]
        deleted = [p for p in cached_dict if p not in current_set]
        modified = []
        for p_str in current_set:
            if p_str in cached_dict:
                old_mtime, old_hash = cached_dict[p_str]
                try:
                    new_mtime, new_hash = self._GetFileMetadata(Path(p_str))
                    if new_mtime != old_mtime or new_hash != old_hash:
                        modified.append(p_str)
                except FileNotFoundError:
                    deleted.append(p_str)

        if not added and not deleted and not modified:
            return False

        try:
            for p_str in deleted:
                self._RemoveProjectsAndToolchainsFromFile(conn, p_str, currentWorkspace)

            for p_str in modified:
                fp = Path(p_str)
                success, updated_projs, updated_tcs = self._LoadExternalFileAndMerge(fp, currentWorkspace, loader)
                if success:
                    mtime, fhash = self._GetFileMetadata(fp)
                    conn.execute(
                        "INSERT OR REPLACE INTO files (path, mtime, hash, last_loaded) VALUES (?, ?, ?, ?)",
                        (p_str, mtime, fhash, now)
                    )
                    for proj_name in updated_projs:
                        proj = currentWorkspace.projects[proj_name]
                        proj_json = json.dumps({'name': proj.name, 'kind': proj.kind.value if proj.kind else ''})
                        conn.execute(
                            "INSERT OR REPLACE INTO projects (name, source_file, project_json, updated_at) VALUES (?, ?, ?, ?)",
                            (proj_name, p_str, proj_json, now)
                        )
                    for tc_name in updated_tcs:
                        tc = currentWorkspace.toolchains[tc_name]
                        tc_json = json.dumps({'name': tc.name, 'compilerFamily': tc.compilerFamily.value if tc.compilerFamily else ''})
                        conn.execute(
                            "INSERT OR REPLACE INTO toolchains (name, source_file, toolchain_json, updated_at) VALUES (?, ?, ?, ?)",
                            (tc_name, p_str, tc_json, now)
                        )

            for p_str in added:
                fp = Path(p_str)
                success, updated_projs, updated_tcs = self._LoadExternalFileAndMerge(fp, currentWorkspace, loader)
                if success:
                    mtime, fhash = self._GetFileMetadata(fp)
                    conn.execute(
                        "INSERT OR REPLACE INTO files (path, mtime, hash, last_loaded) VALUES (?, ?, ?, ?)",
                        (p_str, mtime, fhash, now)
                    )
                    for proj_name in updated_projs:
                        proj = currentWorkspace.projects[proj_name]
                        proj_json = json.dumps({'name': proj.name, 'kind': proj.kind.value if proj.kind else ''})
                        conn.execute(
                            "INSERT OR REPLACE INTO projects (name, source_file, project_json, updated_at) VALUES (?, ?, ?, ?)",
                            (proj_name, p_str, proj_json, now)
                        )
                    for tc_name in updated_tcs:
                        tc = currentWorkspace.toolchains[tc_name]
                        tc_json = json.dumps({'name': tc.name, 'compilerFamily': tc.compilerFamily.value if tc.compilerFamily else ''})
                        conn.execute(
                            "INSERT OR REPLACE INTO toolchains (name, source_file, toolchain_json, updated_at) VALUES (?, ?, ?, ?)",
                            (tc_name, p_str, tc_json, now)
                        )

            workspace_json = self._SerializeWorkspace(currentWorkspace)
            conn.execute(
                "INSERT OR REPLACE INTO workspace (key, value, updated_at) VALUES (?, ?, ?)",
                ("workspace", workspace_json, now)
            )
            conn.execute("UPDATE metadata SET updated_at=? WHERE version=1", (now,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        return True

    def Invalidate(self) -> None:
        """Supprime la base de données (--no-cache)."""
        # Fermer la connexion avant de supprimer le fichier
        self.Close()
        if self.dbPath.exists():
            try:
                self.dbPath.unlink()
                Colored.PrintInfo(f"Cache invalidated: {self.dbPath}")
            except PermissionError:
                Colored.PrintWarning(f"Could not delete cache file (may be locked): {self.dbPath}")

    def Close(self) -> None:
        """Ferme la connexion SQLite."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Close()
