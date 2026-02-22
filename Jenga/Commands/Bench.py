#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bench command – Lance des benchmarks automatisés.
Utilise Google Benchmark, Catch2, ou scripts personnalisés.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from ..Utils import Colored, Display, FileSystem, Process
from ..Core.Loader import Loader
from ..Core.Cache import Cache
from ..Core import Api


class BenchCommand:
    """jenga bench [--project PROJECT] [--config CONFIG] [--platform PLATFORM] [--iterations N] [--output FILE]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga bench", description="Run benchmarks.")
        parser.add_argument("--project", help="Benchmark project to run")
        parser.add_argument("--config", default="Release", help="Build configuration")
        parser.add_argument("--platform", default=None, help="Target platform")
        parser.add_argument("--iterations", type=int, default=10, help="Number of iterations")
        parser.add_argument("--output", "-o", default="./bench_results.json", help="Output file for results")
        parser.add_argument("--no-daemon", action="store_true")
        parser.add_argument("--verbose", "-v", action="store_true")
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

        # Charger workspace
        loader = Loader(verbose=parsed.verbose)
        cache = Cache(workspace_root, workspaceName=entry_file.stem)
        workspace = cache.LoadWorkspace(entry_file, loader)
        if workspace is None:
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace:
                cache.SaveWorkspace(workspace, entry_file, loader)
        if workspace is None:
            return 1

        # Déterminer le projet benchmark
        project_name = parsed.project
        if not project_name:
            # Chercher un projet de type test ou ayant des fichiers de benchmark
            for name, proj in workspace.projects.items():
                if 'bench' in name.lower() or (hasattr(proj, 'isBench') and proj.isBench):
                    project_name = name
                    break
        if not project_name:
            # Fallback pragmatique: utiliser startProject si exécutable.
            candidate = workspace.startProject
            if candidate and candidate in workspace.projects:
                candidate_proj = workspace.projects[candidate]
                if candidate_proj.kind in (
                    Api.ProjectKind.CONSOLE_APP,
                    Api.ProjectKind.WINDOWED_APP,
                    Api.ProjectKind.TEST_SUITE,
                ):
                    project_name = candidate
                    Colored.PrintWarning(
                        f"No dedicated benchmark project found. Falling back to start project '{project_name}'."
                    )
        if not project_name:
            # Dernier fallback: premier exécutable.
            for name, proj in workspace.projects.items():
                if proj.kind in (
                    Api.ProjectKind.CONSOLE_APP,
                    Api.ProjectKind.WINDOWED_APP,
                    Api.ProjectKind.TEST_SUITE,
                ):
                    project_name = name
                    Colored.PrintWarning(
                        f"No dedicated benchmark project found. Falling back to executable project '{project_name}'."
                    )
                    break
        if not project_name:
            Colored.PrintError("No benchmark project found.")
            return 1

        # Build le projet
        from .build import BuildCommand
        build_args = ["--config", parsed.config, "--action", "bench", "--target", project_name]
        if parsed.platform:
            build_args += ["--platform", parsed.platform]
        if parsed.jenga_file:
            build_args += ["--jenga-file", str(entry_file)]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        # Exécuter le benchmark
        # On suppose que l'exécutable supporte --benchmark_out=...
        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, parsed.platform, project_name, parsed.verbose,
            action="bench",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform=parsed.platform,
                target=project_name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=["action:bench"]
            )
        )
        exe_path = builder.GetTargetPath(workspace.projects[project_name])
        if not exe_path.exists():
            # Fallback: locate the newest matching artifact in Build/.
            build_root = Path(workspace.location) / "Build"
            base_name = workspace.projects[project_name].targetName or project_name
            candidates = []
            if build_root.exists():
                for ext in [".exe", "", ".js"]:
                    candidates.extend(build_root.rglob(f"{base_name}{ext}"))
            candidates = [p for p in candidates if p.is_file()]
            if candidates:
                candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                exe_path = candidates[0]
            else:
                Colored.PrintError(f"Benchmark executable not found: {exe_path}")
                return 1

        cmd = [str(exe_path), f"--benchmark_out={parsed.output}", f"--benchmark_repetitions={parsed.iterations}"]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        if result.returnCode == 0:
            Colored.PrintSuccess(f"Benchmark results saved to {parsed.output}")
        return result.returnCode
