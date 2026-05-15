#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watch command – Surveille les fichiers et rebuild automatiquement.
Démarre le daemon si nécessaire, puis active le watcher.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

from ..Utils import Colored, FileSystem


class WatchCommand:
    """jenga watch [--config NAME] [--platform NAME] [--polling] [--no-daemon]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga watch", description="Watch files and rebuild automatically.")
        parser.add_argument("--config", default="Debug", help="Build configuration")
        parser.add_argument("--platform", default=None, help="Target platform")
        parser.add_argument("--polling", action="store_true", help="Use polling instead of watchdog")
        parser.add_argument("--no-daemon", action="store_true", help="Do not use daemon (run in foreground)")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--jenga-file", help="Path to the workspace .jenga file (default: auto-detected)")
        parsed = parser.parse_args(args)

        # Déterminer le répertoire de travail (workspace root)
        workspace_root = Path.cwd()
        if parsed.jenga_file:
            entry_file = Path(parsed.jenga_file).resolve()
            if not entry_file.exists():
                Colored.PrintError(f"Jenga file not found: {entry_file}")
                return 1
        else:
            entry_file = FileSystem.FindWorkspaceEntry(workspace_root)
            if not entry_file:
                Colored.PrintError("No .jenga workspace file found.")
                return 1
        workspace_root = entry_file.parent

        # Si --no-daemon, on exécute un watcher local (sans daemon)
        if parsed.no_daemon:
            Colored.PrintInfo("Starting local watcher (no daemon)...")
            from ..Core.Watcher import FileWatcher
            from ..Core.Loader import Loader
            from ..Core.Cache import Cache
            from .Build import BuildCommand

            watcher = FileWatcher(use_polling=parsed.polling)
            watcher.AddWatch(workspace_root)

            def on_change(event_type, path):
                Colored.PrintInfo(f"File changed: {path}")
                # Rebuild
                build_args = ["--config", parsed.config]
                if parsed.platform:
                    build_args += ["--platform", parsed.platform]
                if parsed.jenga_file:
                    build_args += ["--jenga-file", str(entry_file)]
                if parsed.verbose:
                    build_args.append("--verbose")
                BuildCommand.Execute(build_args)

            watcher.AddCallback(on_change)
            watcher.Start()
            Colored.PrintInfo("Watching for file changes... Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                watcher.Stop()
                return 0

        # Avec daemon
        # Vérifier si le daemon tourne
        from ..Core.Daemon import DaemonClient, StartDaemon, DaemonStatus, StopDaemon
        status = DaemonStatus(workspace_root)
        if not status.get('running'):
            Colored.PrintInfo("Starting daemon...")
            if not StartDaemon(workspace_root, entry_file, foreground=False):
                Colored.PrintError("Failed to start daemon.")
                return 1
            time.sleep(0.5)  # laisser le temps au daemon de démarrer

        client = DaemonClient(workspace_root)
        if not client.IsAvailable():
            Colored.PrintError("Daemon not available.")
            return 1

        # Démarrer le watcher via le daemon
        try:
            response = client.SendCommand('watch_start', {
                'polling': parsed.polling,
                'config': parsed.config,
                'platform': parsed.platform
            })
            if response.get('status') == 'ok':
                Colored.PrintSuccess("Watcher started. Press Ctrl+C to stop.")
                # Boucle pour garder le processus en vie
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    # Arrêter le watcher
                    client.SendCommand('watch_stop')
                    # Optionnellement arrêter le daemon
                    StopDaemon(workspace_root)
                    return 0
            else:
                Colored.PrintError(f"Failed to start watcher: {response.get('message')}")
                return 1
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            Colored.PrintError(f"Daemon communication error: {e}")
            return 1
