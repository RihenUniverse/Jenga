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
        parser.add_argument("--platform", required=True, choices=['windows', 'linux', 'macos', 'android', 'ios', 'tvos', 'watchos'],
                            help="Target platform")
        parser.add_argument("--ios-builder", choices=["direct", "xcode", "xbuilder"], default=None,
                            help="Apple mobile builder backend (direct or xcode/xbuilder).")
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
        if project_name not in workspace.projects:
            Colored.PrintError(f"Project '{project_name}' not found.")
            return 1
        project = workspace.projects[project_name]

        # Construire le projet
        from .Build import BuildCommand
        build_args = ["--config", parsed.config, "--platform", parsed.platform, "--target", project_name]
        if parsed.ios_builder and parsed.platform in ("ios", "tvos", "watchos"):
            build_args += [f"--ios-builder={parsed.ios_builder}"]
        if parsed.jenga_file:
            build_args += ["--jenga-file", str(entry_file)]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        # Lancer le profiler selon plateforme
        if parsed.platform == 'windows':
            return ProfileCommand._ProfileWindows(parsed)
        elif parsed.platform == 'linux':
            return ProfileCommand._ProfileLinux(workspace, project, parsed)
        elif parsed.platform == 'macos':
            return ProfileCommand._ProfileMacOS(parsed)
        elif parsed.platform == 'android':
            return ProfileCommand._ProfileAndroid(parsed)
        elif parsed.platform in ('ios', 'tvos', 'watchos'):
            return ProfileCommand._ProfileIOS(parsed)
        else:
            return 1

    @staticmethod
    def _ProfileWindows(parsed):
        """Utilise Windows Performance Toolkit (xperf, WPR, WPA) ou Visual Studio Profiler."""
        Colored.PrintWarning("Windows profiling not yet implemented.")
        return 1

    @staticmethod
    def _ProfileLinux(workspace, project, parsed):
        """Profile Linux with perf when available, otherwise run-based fallback."""
        from .Build import BuildCommand

        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, "linux", project.name, parsed.verbose,
            action="profile",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform="linux",
                target=project.name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=["action:profile", "profile:linux"]
            )
        )

        exe_path = builder.GetTargetPath(project)
        if not exe_path.exists():
            Colored.PrintError(f"Profile executable not found: {exe_path}")
            return 1

        output_dir = Path(parsed.output).resolve()
        FileSystem.MakeDirectory(output_dir)

        selected_tool = (parsed.tool or "").strip().lower()
        perf_path = FileSystem.FindExecutable("perf")
        if not selected_tool:
            selected_tool = "perf" if perf_path else "run"

        if selected_tool == "perf":
            if not perf_path:
                Colored.PrintWarning("perf not found. Falling back to runtime profiling.")
                selected_tool = "run"
            else:
                perf_data = output_dir / f"{project.name}.perf.data"
                perf_report = output_dir / f"{project.name}.perf.txt"
                cmd = [perf_path, "record", "-g", "-o", str(perf_data), "--", str(exe_path)]

                timeout_bin = FileSystem.FindExecutable("timeout")
                if parsed.duration and timeout_bin:
                    cmd = [timeout_bin, str(parsed.duration)] + cmd

                result = Process.ExecuteCommand(cmd, captureOutput=True, cwd=exe_path.parent)
                if result.returnCode not in (0, 124):
                    Colored.PrintError("perf record failed.")
                    if result.stderr:
                        Colored.PrintError(result.stderr.strip())
                    return 1

                if perf_data.exists():
                    report = Process.ExecuteCommand(
                        [perf_path, "report", "-i", str(perf_data), "--stdio"],
                        captureOutput=True,
                        cwd=exe_path.parent
                    )
                    perf_report.write_text(report.stdout or "", encoding="utf-8")
                    Colored.PrintSuccess(f"Perf data: {perf_data}")
                    Colored.PrintSuccess(f"Perf report: {perf_report}")
                    return 0

                Colored.PrintError("perf data file was not generated.")
                return 1

        # Generic runtime fallback.
        run_log = output_dir / f"{project.name}.runtime.log"
        try:
            result = Process.ExecuteCommand(
                [str(exe_path)],
                captureOutput=True,
                cwd=exe_path.parent,
                timeout=max(1, parsed.duration or 30)
            )
            run_log.write_text((result.stdout or "") + ("\n" + result.stderr if result.stderr else ""), encoding="utf-8")
            if result.returnCode != 0:
                Colored.PrintError(f"Application exited with code {result.returnCode}.")
                return 1
        except TimeoutError:
            run_log.write_text("Profiling timeout reached; process terminated.\n", encoding="utf-8")
            Colored.PrintWarning(f"Profiling stopped after timeout ({parsed.duration}s).")

        Colored.PrintSuccess(f"Runtime profile log: {run_log}")
        return 0

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
