#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy command – Déploie l'application sur des appareils (consoles, mobiles) ou sur des stores/testers.
Support : Android (adb), iOS (ios-deploy), Xbox (xbapp), etc.
"""

import argparse
import sys, shutil, os
from pathlib import Path
from typing import List

from ..Utils import Colored, Display, FileSystem, Process
from ..Core.Loader import Loader
from ..Core.Cache import Cache
from ..Core import Api


class DeployCommand:
    """jenga deploy [--platform PLATFORM] [--target DEVICE] [--config CONFIG] [--project PROJECT]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga deploy", description="Deploy app to device or store.")
        parser.add_argument("--platform", required=True, choices=['android', 'ios', 'xbox', 'linux', 'macos', 'windows'],
                            help="Target platform")
        parser.add_argument("--target", help="Device identifier (IP address, UDID, etc.)")
        parser.add_argument("--config", default="Release", help="Build configuration")
        parser.add_argument("--project", help="Project to deploy (default: first executable)")
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

        # Charger le workspace
        loader = Loader(verbose=parsed.verbose)
        cache = Cache(workspace_root, workspaceName=entry_file.stem)

        if parsed.no_daemon:
            workspace = loader.LoadWorkspace(str(entry_file))
        else:
            from ..Core.Daemon import DaemonClient
            client = DaemonClient(workspace_root)
            if client.IsAvailable():
                try:
                    response = client.SendCommand('deploy', {
                        'platform': parsed.platform,
                        'target': parsed.target,
                        'config': parsed.config,
                        'project': parsed.project,
                        'verbose': parsed.verbose
                    })
                    if response.get('status') == 'ok':
                        return response.get('return_code', 0)
                    else:
                        Colored.PrintError(f"Daemon deploy failed: {response.get('message')}")
                        return 1
                except Exception as e:
                    Colored.PrintWarning(f"Daemon error: {e}, falling back.")
            workspace = cache.LoadWorkspace(entry_file, loader)
            if workspace is None:
                workspace = loader.LoadWorkspace(str(entry_file))
                if workspace:
                    cache.SaveWorkspace(workspace, entry_file, loader)

        if workspace is None:
            Colored.PrintError("Failed to load workspace.")
            return 1

        # Déterminer le projet
        project_name = parsed.project or workspace.startProject
        if not project_name:
            for name, proj in workspace.projects.items():
                if proj.kind in (Api.ProjectKind.CONSOLE_APP, Api.ProjectKind.WINDOWED_APP):
                    project_name = name
                    break
        if not project_name or project_name not in workspace.projects:
            Colored.PrintError(f"Project '{project_name}' not found.")
            return 1

        project = workspace.projects[project_name]

        # Appeler la méthode de déploiement selon plateforme
        if parsed.platform == 'android':
            return DeployCommand._DeployAndroid(workspace, project, parsed)
        elif parsed.platform == 'ios':
            return DeployCommand._DeployIOS(workspace, project, parsed)
        elif parsed.platform == 'xbox':
            return DeployCommand._DeployXbox(workspace, project, parsed)
        elif parsed.platform == 'linux':
            return DeployCommand._DeployLinux(workspace, project, parsed)
        elif parsed.platform == 'macos':
            return DeployCommand._DeployMacOS(workspace, project, parsed)
        elif parsed.platform == 'windows':
            return DeployCommand._DeployWindows(workspace, project, parsed)
        else:
            Colored.PrintError(f"Deploy for platform '{parsed.platform}' not implemented.")
            return 1

    @staticmethod
    def _DeployAndroid(workspace, project, parsed):
        """Déploiement sur appareil Android via adb."""
        sdk_path = workspace.androidSdkPath or os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        if not sdk_path:
            Colored.PrintError("Android SDK not found. Set androidSdkPath in workspace.")
            return 1

        adb = Path(sdk_path) / "platform-tools" / "adb"
        if not adb.exists():
            adb = Path(sdk_path) / "adb"
        if not adb.exists():
            adb = FileSystem.FindExecutable("adb")
        if not adb:
            Colored.PrintError("adb not found.")
            return 1

        # Construire l'APK si nécessaire
        from .Build import BuildCommand
        build_args = ["--config", parsed.config, "--platform", "Android", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        # Localiser l'APK
        builder = BuildCommand.CreateBuilder(workspace, parsed.config, "Android", project.name, parsed.verbose)
        apk_path = builder.GetTargetDir(project) / f"{project.targetName or project.name}.apk"
        if not apk_path.exists():
            Colored.PrintError(f"APK not found: {apk_path}")
            return 1

        # Installer via adb
        target = parsed.target
        cmd = [str(adb)]
        if target:
            cmd += ["-s", target]
        cmd += ["install", "-r", str(apk_path)]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        if result.returnCode == 0:
            Colored.PrintSuccess("APK installed successfully.")
            return 0
        else:
            Colored.PrintError("adb install failed.")
            return 1

    @staticmethod
    def _DeployIOS(workspace, project, parsed):
        """Déploiement sur simulateur ou périphérique iOS."""
        if Api.Platform.GetHostOS() != Api.TargetOS.MACOS:
            Colored.PrintError("iOS deployment requires macOS.")
            return 1

        # Utiliser ios-deploy
        ios_deploy = FileSystem.FindExecutable("ios-deploy")
        if not ios_deploy:
            Colored.PrintError("ios-deploy not found. Install with: brew install ios-deploy")
            return 1

        # Build project
        from .Build import BuildCommand
        build_args = ["--config", parsed.config, "--platform", "iOS", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        builder = BuildCommand.CreateBuilder(workspace, parsed.config, "iOS", project.name, parsed.verbose)
        app_bundle = builder.GetTargetDir(project) / f"{project.targetName or project.name}.app"
        if not app_bundle.exists():
            Colored.PrintError(f".app bundle not found: {app_bundle}")
            return 1

        cmd = [ios_deploy, "--bundle", str(app_bundle)]
        if parsed.target:
            cmd += ["--id", parsed.target]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return 0 if result.returnCode == 0 else 1

    @staticmethod
    def _DeployXbox(workspace, project, parsed):
        """Déploiement sur Xbox via xbapp."""
        # Vérifier que le builder Xbox est disponible
        try:
            from ..Core.Builders.Xbox import XboxBuilder
        except ImportError:
            Colored.PrintError("XboxBuilder not available.")
            return 1

        from .Build import BuildCommand
        build_args = ["--config", parsed.config, "--platform", "Xbox", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        builder = BuildCommand.CreateBuilder(workspace, parsed.config, "Xbox", project.name, parsed.verbose)
        layout_dir = builder.GetTargetDir(project) / builder.xbox_platform
        if not layout_dir.exists():
            Colored.PrintError("Xbox layout directory not found.")
            return 1

        return 0 if builder.DeployToConsole(project, layout_dir, parsed.target) else 1

    @staticmethod
    def _DeployLinux(workspace, project, parsed):
        """Déploiement sur Linux (copie SSH ou exécution locale)."""
        Colored.PrintWarning("Linux deployment not yet implemented.")
        return 1

    @staticmethod
    def _DeployMacOS(workspace, project, parsed):
        """Déploiement sur macOS (copie locale)."""
        from .Build import BuildCommand
        build_args = ["--config", parsed.config, "--platform", "macOS", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1
        builder = BuildCommand.CreateBuilder(workspace, parsed.config, "macOS", project.name, parsed.verbose)
        app_bundle = builder.GetTargetDir(project) / f"{project.targetName or project.name}.app"
        if app_bundle.exists():
            Colored.PrintInfo(f"Application built at: {app_bundle}")
            # Option: copier vers /Applications
            if parsed.target == "/Applications":
                dest = Path("/Applications") / app_bundle.name
                shutil.copytree(app_bundle, dest, dirs_exist_ok=True)
                Colored.PrintSuccess(f"App installed to {dest}")
                return 0
        return 0

    @staticmethod
    def _DeployWindows(workspace, project, parsed):
        """Déploiement sur Windows (copie locale)."""
        from .Build import BuildCommand
        build_args = ["--config", parsed.config, "--platform", "Windows", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1
        builder = BuildCommand.CreateBuilder(workspace, parsed.config, "Windows", project.name, parsed.verbose)
        exe_path = builder.GetTargetPath(project)
        if exe_path.exists():
            Colored.PrintInfo(f"Executable built at: {exe_path}")
        return 0    
