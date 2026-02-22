#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run command – Exécute l'exécutable d'un projet (après build si nécessaire).
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from ..Core.Loader import Loader
from ..Core.Cache import Cache
from ..Core.Builder import Builder
from ..Core import Api
from ..Utils import Colored, Process, FileSystem
from .build import BuildCommand


class RunCommand:
    """jenga run [PROJECT] [--config NAME] [--platform NAME] [--args ...]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga run", description="Run a project executable.")
        parser.add_argument("project", nargs="?", default=None, help="Project name to run (default: startProject or first executable)")
        parser.add_argument("--config", default="Debug", help="Build configuration")
        parser.add_argument("--platform", default=None, help="Target platform")
        parser.add_argument("--args", nargs=argparse.REMAINDER, default=[], help="Arguments to pass to the executable")
        parser.add_argument("--no-build", action="store_true", help="Skip build step (assume already built)")
        parser.add_argument("--no-daemon", action="store_true", help="Do not use daemon")
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

        # Utiliser le daemon si disponible
        if not parsed.no_daemon:
            from ..Core.Daemon import DaemonClient, DaemonStatus
            client = DaemonClient(workspace_root)
            if client.IsAvailable():
                try:
                    response = client.SendCommand('run', {
                        'project': parsed.project,
                        'config': parsed.config,
                        'platform': parsed.platform,
                        'args': parsed.args,
                        'no_build': parsed.no_build
                    })
                    if response.get('status') == 'ok':
                        return response.get('return_code', 0)
                    else:
                        Colored.PrintError(f"Daemon run failed: {response.get('message')}")
                        return 1
                except Exception as e:
                    Colored.PrintWarning(f"Daemon error: {e}, falling back.")

        # Mode direct
        loader = Loader(verbose=False)
        cache = Cache(workspace_root)
        workspace = cache.LoadWorkspace(entry_file, loader)
        if workspace is None:
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace:
                cache.SaveWorkspace(workspace, entry_file, loader)
            else:
                Colored.PrintError("Failed to load workspace.")
                return 1

        # Déterminer le projet à exécuter
        project_name = parsed.project
        if not project_name:
            project_name = workspace.startProject
        if not project_name:
            # Chercher le premier projet de type exécutable
            for name, proj in workspace.projects.items():
                if proj.kind in (Api.ProjectKind.CONSOLE_APP, Api.ProjectKind.WINDOWED_APP, Api.ProjectKind.TEST_SUITE):
                    project_name = name
                    break
        if not project_name:
            Colored.PrintError("No executable project found.")
            return 1

        if project_name not in workspace.projects:
            Colored.PrintError(f"Project '{project_name}' not found.")
            return 1

        project = workspace.projects[project_name]

        # Build si nécessaire
        if not parsed.no_build:
            Colored.PrintInfo(f"Building {project_name}...")
            build_args = ["--config", parsed.config]
            build_args += ["--action", "run"]
            if parsed.platform:
                build_args += ["--platform", parsed.platform]
            if parsed.jenga_file:
                build_args += ["--jenga-file", str(entry_file)]
            build_args += ["--target", project_name]
            ret = BuildCommand.Execute(build_args)
            if ret != 0:
                return ret

        # Déterminer le chemin de l'exécutable
        # Il faut un builder pour connaître l'extension et le chemin exact
        try:
            builder = BuildCommand.CreateBuilder(
                workspace,
                config=parsed.config,
                platform=parsed.platform or (workspace.targetOses[0].value if workspace.targetOses else "Windows"),
                target=project_name,
                verbose=False,
                action="run",
                options=BuildCommand.CollectFilterOptions(
                    config=parsed.config,
                    platform=parsed.platform,
                    target=project_name,
                    verbose=False,
                    no_cache=False,
                    no_daemon=parsed.no_daemon,
                    extra=["action:run"]
                )
            )
        except Exception as e:
            Colored.PrintError(f"Cannot create builder: {e}")
            return 1

        exe_path = builder.GetTargetPath(project)
        if not exe_path.exists():
            Colored.PrintError(f"Executable not found: {exe_path}")
            return 1

        # Exécuter
        Colored.PrintInfo(f"Running {exe_path}...")
        cmd = [str(exe_path)] + parsed.args
        return Process.Run(cmd)
