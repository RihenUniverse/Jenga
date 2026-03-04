#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watcher – Surveillance des fichiers .jenga et des sources.
Notifie des changements (création, modification, suppression) via des callbacks.
Utilise watchdog si disponible, sinon polling.

Toutes les méthodes publiques sont en PascalCase.
"""

import os
import time
from pathlib import Path
from typing import Set, List, Callable, Optional, Union
from threading import Thread, Event

from ..Utils import Colored, FileSystem

# ✅ Import absolu cohérent avec l'API utilisateur
from Jenga.Core import Api


class FileWatcher:
    """
    Surveille des répertoires ou des fichiers et exécute des callbacks
    sur les événements.
    """

    def __init__(self, use_polling: bool = False, polling_interval: float = 1.0):
        self.use_polling = use_polling
        self.polling_interval = polling_interval
        self._callbacks = []
        self._watch_paths = set()
        self._ignore_patterns = ['.git', '.jenga', '__pycache__', '*.pyc', '*.swp', '*.swx', '*.tmp']
        self._running = False
        self._thread = None
        self._stop_event = Event()
        self._watchdog_available = False
        self._Observer = None
        self._FileSystemEventHandler = None

        if not use_polling:
            try:
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler
                self._Observer = Observer
                self._FileSystemEventHandler = FileSystemEventHandler
                self._watchdog_available = True
            except ImportError:
                Colored.PrintWarning(
                    "watchdog module not installed. Falling back to polling mode.\n"
                    "Install watchdog for better performance: pip install watchdog"
                )
                self.use_polling = True

    # -----------------------------------------------------------------------
    # Gestion des callbacks et des chemins
    # -----------------------------------------------------------------------

    def AddCallback(self, callback: Callable[[str, str], None]) -> None:
        """
        Ajoute un callback qui sera appelé sur chaque événement.
        Signature: callback(event_type: str, path: str)
        event_type: 'created', 'modified', 'deleted'
        """
        self._callbacks.append(callback)

    def AddWatch(self, path: Union[str, Path], recursive: bool = True) -> None:
        """Ajoute un chemin à surveiller."""
        p = Path(path).resolve()
        if p.exists():
            self._watch_paths.add(str(p))
        else:
            Colored.PrintWarning(f"Path does not exist, cannot watch: {p}")

    def AddIgnorePattern(self, pattern: str) -> None:
        """Ajoute un pattern de fichiers/dossiers à ignorer."""
        self._ignore_patterns.append(pattern)

    def _ShouldIgnore(self, path: str) -> bool:
        """Vérifie si un chemin doit être ignoré."""
        p = Path(path)
        for pattern in self._ignore_patterns:
            if pattern.startswith('*'):
                if p.name.endswith(pattern[1:]):
                    return True
            elif pattern in p.parts:
                return True
            elif p.match(pattern):
                return True
        return False

    # -----------------------------------------------------------------------
    # Mode watchdog (recommandé)
    # -----------------------------------------------------------------------

    def _StartWatchdog(self) -> None:
        """Démarre la surveillance avec watchdog."""
        class JengaEventHandler(self._FileSystemEventHandler):
            def __init__(self, watcher):
                self.watcher = watcher

            def on_created(self, event):
                if not self.watcher._ShouldIgnore(event.src_path):
                    self.watcher._Notify('created', event.src_path)

            def on_modified(self, event):
                if not self.watcher._ShouldIgnore(event.src_path):
                    self.watcher._Notify('modified', event.src_path)

            def on_deleted(self, event):
                if not self.watcher._ShouldIgnore(event.src_path):
                    self.watcher._Notify('deleted', event.src_path)

            def on_moved(self, event):
                # Traiter comme suppression + création
                if not self.watcher._ShouldIgnore(event.src_path):
                    self.watcher._Notify('deleted', event.src_path)
                if not self.watcher._ShouldIgnore(event.dest_path):
                    self.watcher._Notify('created', event.dest_path)

        self._observer = self._Observer()
        handler = JengaEventHandler(self)
        for path in self._watch_paths:
            self._observer.schedule(handler, path, recursive=True)
        self._observer.start()

    # -----------------------------------------------------------------------
    # Mode polling (fallback)
    # -----------------------------------------------------------------------

    def _StartPolling(self) -> None:
        """Démarre la surveillance par polling."""
        self._snapshots = {}

        def poll_loop():
            while not self._stop_event.is_set():
                for path_str in self._watch_paths:
                    path = Path(path_str)
                    if path.is_dir():
                        self._PollDirectory(path)
                    elif path.is_file():
                        self._PollFile(path)
                self._stop_event.wait(self.polling_interval)

        self._thread = Thread(target=poll_loop, daemon=True)
        self._thread.start()

    def _PollDirectory(self, path: Path) -> None:
        """Surveille un répertoire par polling."""
        current_files = {}
        for root, dirs, files in os.walk(path):
            # Ignorer les réperoires cachés
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.startswith('.'):
                    continue
                full_path = Path(root) / file
                if self._ShouldIgnore(str(full_path)):
                    continue
                try:
                    mtime = full_path.stat().st_mtime
                    current_files[str(full_path)] = mtime
                except OSError:
                    continue

        snapshot_key = str(path)
        old_snapshot = self._snapshots.get(snapshot_key, {})

        # Détection des créations/modifications
        for fp, mtime in current_files.items():
            if fp not in old_snapshot:
                self._Notify('created', fp)
            elif old_snapshot[fp] != mtime:
                self._Notify('modified', fp)

        # Détection des suppressions
        for fp in old_snapshot:
            if fp not in current_files:
                self._Notify('deleted', fp)

        self._snapshots[snapshot_key] = current_files

    def _PollFile(self, path: Path) -> None:
        """Surveille un fichier unique par polling."""
        try:
            mtime = path.stat().st_mtime
            old_mtime = self._snapshots.get(str(path))
            if old_mtime is None:
                self._Notify('created', str(path))
            elif old_mtime != mtime:
                self._Notify('modified', str(path))
            self._snapshots[str(path)] = mtime
        except OSError:
            # Fichier supprimé
            if str(path) in self._snapshots:
                self._Notify('deleted', str(path))
                del self._snapshots[str(path)]

    # -----------------------------------------------------------------------
    # Interface publique
    # -----------------------------------------------------------------------

    def Start(self) -> None:
        """Démarre la surveillance."""
        if not self._watch_paths:
            Colored.PrintWarning("No paths to watch.")
            return

        self._running = True
        self._stop_event.clear()

        if not self.use_polling and self._watchdog_available:
            self._StartWatchdog()
        else:
            self._StartPolling()

    def Stop(self) -> None:
        """Arrête la surveillance."""
        self._running = False
        self._stop_event.set()
        if hasattr(self, '_observer'):
            self._observer.stop()
            self._observer.join()
        if self._thread:
            self._thread.join(timeout=2)

    def _Notify(self, event_type: str, path: str) -> None:
        """Appelle tous les callbacks avec l'événement."""
        for callback in self._callbacks:
            try:
                callback(event_type, path)
            except Exception as e:
                Colored.PrintError(f"Watcher callback error: {e}")

    def __enter__(self):
        self.Start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.Stop()