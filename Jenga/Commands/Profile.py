#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Profile command – Profilage des applications (CPU, mémoire, etc.)
Utilise des outils spécifiques à la plateforme (perf, Instruments, Visual Studio Profiler, etc.)
"""

import argparse
import sys
from pathlib import Path
from typing import List

from ..Utils import Colored, Display, FileSystem, Process
from ..Core.Loader import Loader
from ..Core.Cache import Cache


class ProfileCommand:
    """jenga profile [--platform PLATFORM] [--config CONFIG] [--project PROJECT] [--tool TOOL] [--duration SEC]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga profile", description="Profile application performance.")
        parser.add_argument("--platform", required=True, choices=['windows', 'linux', 'macos', 'android', 'ios'],
                            help="Target platform")
        parser.add_argument("--config", default="Release", help="Build configuration")
        parser.add_argument("--project", help="Project to profile")
        parser.add_argument("--tool", help="Profiling tool (auto-detect if omitted)")
        parser.add_argument("--duration", type=int, default=30, help="Profiling duration in seconds")
        parser.add_argument("--output", "-o", default="./profile", help="Output directory for profiling data")
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

        # Charger workspace pour trouver le projet
        loader = Loader(verbose=parsed.verbose)
        cache = Cache(workspace_root, workspaceName=entry_file.stem)
        workspace = cache.LoadWorkspace(entry_file, loader)
        if workspace is None:
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace:
                cache.SaveWorkspace(workspace, entry_file, loader)
        if workspace is None:
            return 1

        # Déterminer projet
        project_name = parsed.project or workspace.startProject
        if not project_name:
            Colored.PrintError("No project specified.")
            return 1

        # Construire le projet
        from .Build import BuildCommand
        build_args = ["--config", parsed.config, "--platform", parsed.platform, "--target", project_name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", str(entry_file)]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        # Lancer le profiler selon plateforme
        if parsed.platform == 'windows':
            return ProfileCommand._ProfileWindows(parsed)
        elif parsed.platform == 'linux':
            return ProfileCommand._ProfileLinux(parsed)
        elif parsed.platform == 'macos':
            return ProfileCommand._ProfileMacOS(parsed)
        elif parsed.platform == 'android':
            return ProfileCommand._ProfileAndroid(parsed)
        elif parsed.platform == 'ios':
            return ProfileCommand._ProfileIOS(parsed)
        else:
            return 1

    @staticmethod
    def _ProfileWindows(parsed):
        """Utilise Windows Performance Toolkit (xperf, WPR, WPA) ou Visual Studio Profiler."""
        Colored.PrintWarning("Windows profiling not yet implemented.")
        return 1

    @staticmethod
    def _ProfileLinux(parsed):
        """Utilise perf, valgrind, gprof."""
        if not parsed.tool:
            parsed.tool = "perf"
        if parsed.tool == "perf":
            # Vérifier la présence
            if not FileSystem.FindExecutable("perf"):
                Colored.PrintError("perf not found. Install linux-tools-common.")
                return 1
            # Lancer l'exécutable avec perf record
            # Il faut trouver le binaire
            # Simplifié: on suppose qu'on connaît le chemin
            Colored.PrintInfo(f"Profiling with perf for {parsed.duration}s...")
            cmd = ["perf", "record", "-g", "--", "./myapp"]  # TODO: remplacer par chemin réel
            if parsed.duration:
                cmd = ["timeout", str(parsed.duration)] + cmd
            Process.Run(cmd)
            Colored.PrintInfo("Generating perf report...")
            Process.Run(["perf", "report", "-g", "graph"])
            return 0
        return 1

    @staticmethod
    def _ProfileMacOS(parsed):
        """Utilise Instruments (xctrace)."""
        if not FileSystem.FindExecutable("xctrace"):
            Colored.PrintError("xctrace not found. Install Xcode command line tools.")
            return 1
        Colored.PrintInfo("Profiling with Instruments...")
        # xctrace record --template 'Time Profiler' --output ./profile.trace --attach <pid>
        # Pour l'instant, stub
        Colored.PrintWarning("macOS profiling not yet fully implemented.")
        return 1

    @staticmethod
    def _ProfileAndroid(parsed):
        """Utilise Android Studio Profiler ou simpleperf."""
        Colored.PrintWarning("Android profiling not yet implemented.")
        return 1

    @staticmethod
    def _ProfileIOS(parsed):
        """Utilise Instruments sur iOS."""
        Colored.PrintWarning("iOS profiling not yet implemented.")
        return 1
