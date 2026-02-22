#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy command â€“ DÃ©ploie l'application sur des appareils (consoles, mobiles) ou sur des stores/testers.
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
        parser.add_argument("--platform", required=True, choices=['android', 'ios', 'tvos', 'watchos', 'xbox', 'linux', 'macos', 'windows'],
                            help="Target platform")
        parser.add_argument("--ios-builder", choices=["direct", "xcode", "xbuilder"], default=None,
                            help="Apple mobile builder backend (direct or xcode/xbuilder).")
        parser.add_argument("--target", help="Device identifier (IP address, UDID, etc.)")
        parser.add_argument("--config", default="Release", help="Build configuration")
        parser.add_argument("--project", help="Project to deploy (default: first executable)")
        parser.add_argument("--no-daemon", action="store_true")
        parser.add_argument("--verbose", "-v", action="store_true")
        parser.add_argument("--jenga-file", help="Path to the workspace .jenga file (default: auto-detected)")
        parsed = parser.parse_args(args)

        # DÃ©terminer le rÃ©pertoire de travail (workspace root)
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

        workspace = None
        if not parsed.no_daemon:
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

        if workspace is None:
            workspace = cache.LoadWorkspace(entry_file, loader)
        if workspace is None:
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace:
                cache.SaveWorkspace(workspace, entry_file, loader)

        if workspace is None:
            Colored.PrintError("Failed to load workspace.")
            return 1

        # DÃ©terminer le projet
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

        # Appeler la mÃ©thode de dÃ©ploiement selon plateforme
        if parsed.platform == 'android':
            return DeployCommand._DeployAndroid(workspace, project, parsed)
        elif parsed.platform in ('ios', 'tvos', 'watchos'):
            return DeployCommand._DeployIOS(workspace, project, parsed, parsed.platform)
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
        """DÃ©ploiement sur appareil Android via adb."""
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

        # Construire l'APK si nÃ©cessaire
        from .build import BuildCommand
        build_args = ["--config", parsed.config, "--action", "deploy", "--platform", "Android", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        # Localiser l'APK
        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, "Android", project.name, parsed.verbose,
            action="deploy",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform="Android",
                target=project.name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=["action:deploy", "deploy:android"]
            )
        )
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
    def _DeployIOS(workspace, project, parsed, apple_platform: str = "ios"):
        """DÃ©ploiement Apple mobile (iOS/tvOS/watchOS)."""
        if Api.Platform.GetHostOS() != Api.TargetOS.MACOS:
            Colored.PrintError("Apple mobile deployment requires macOS.")
            return 1

        platform_token = {
            "ios": "iOS",
            "tvos": "tvOS",
            "watchos": "watchOS",
        }.get((apple_platform or "ios").lower(), "iOS")

        from .build import BuildCommand
        build_args = ["--config", parsed.config, "--action", "deploy", "--platform", platform_token, "--target", project.name]
        if parsed.ios_builder:
            build_args += [f"--ios-builder={parsed.ios_builder}"]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        extra_options = ["action:deploy", f"deploy:{apple_platform.lower()}"]
        if parsed.ios_builder:
            extra_options.append(f"ios-builder={parsed.ios_builder}")

        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, platform_token, project.name, parsed.verbose,
            action="deploy",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform=platform_token,
                target=project.name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=extra_options
            )
        )
        app_bundle = builder.GetTargetDir(project) / f"{project.targetName or project.name}.app"
        if not app_bundle.exists():
            Colored.PrintError(f".app bundle not found: {app_bundle}")
            return 1

        target = (parsed.target or "").strip()

        # iOS physical device path via ios-deploy (if available).
        if apple_platform.lower() == "ios":
            ios_deploy = FileSystem.FindExecutable("ios-deploy")
            if ios_deploy:
                cmd = [ios_deploy, "--bundle", str(app_bundle)]
                if target:
                    cmd += ["--id", target]
                result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
                if result.returnCode == 0:
                    return 0
                Colored.PrintWarning("ios-deploy failed, trying simulator deployment with simctl.")

        xcrun = FileSystem.FindExecutable("xcrun")
        if not xcrun:
            Colored.PrintError("xcrun not found. Install Xcode command line tools.")
            return 1

        sim_target = target or "booted"
        result_install = Process.ExecuteCommand(
            [xcrun, "simctl", "install", sim_target, str(app_bundle)],
            captureOutput=False,
            silent=False
        )
        if result_install.returnCode != 0:
            Colored.PrintError("simctl install failed.")
            return 1

        bundle_id = (project.iosBundleId or "").strip()
        if bundle_id:
            Process.ExecuteCommand([xcrun, "simctl", "launch", sim_target, bundle_id], captureOutput=False, silent=False)
        return 0

    @staticmethod
    def _DeployXbox(workspace, project, parsed):
        """DÃ©ploiement sur Xbox via xbapp."""
        # VÃ©rifier que le builder Xbox est disponible
        try:
            from ..Core.Builders.Xbox import XboxBuilder
        except ImportError:
            Colored.PrintError("XboxBuilder not available.")
            return 1

        from .build import BuildCommand
        build_args = ["--config", parsed.config, "--action", "deploy", "--platform", "Xbox", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, "Xbox", project.name, parsed.verbose,
            action="deploy",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform="Xbox",
                target=project.name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=["action:deploy", "deploy:xbox"]
            )
        )
        layout_dir = builder.GetTargetDir(project) / builder.xbox_platform
        if not layout_dir.exists():
            Colored.PrintError("Xbox layout directory not found.")
            return 1

        return 0 if builder.DeployToConsole(project, layout_dir, parsed.target) else 1

    @staticmethod
    def _DeployLinux(workspace, project, parsed):
        """Déploiement Linux: build + export local/remote."""
        from .build import BuildCommand
        build_args = ["--config", parsed.config, "--action", "deploy", "--platform", "Linux", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1

        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, "Linux", project.name, parsed.verbose,
            action="deploy",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform="Linux",
                target=project.name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=["action:deploy", "deploy:linux"]
            )
        )
        exe_path = builder.GetTargetPath(project)
        if not exe_path.exists():
            Colored.PrintError(f"Executable not found: {exe_path}")
            return 1

        target = (parsed.target or "").strip()
        if not target:
            Colored.PrintSuccess(f"Linux deploy ready: {exe_path}")
            return 0

        # Remote copy (simple form user@host:/path).
        if ":" in target and not target.startswith("/"):
            scp = FileSystem.FindExecutable("scp")
            if not scp:
                Colored.PrintError("scp not found for remote Linux deployment.")
                return 1
            result = Process.ExecuteCommand([scp, str(exe_path), target], captureOutput=False, silent=False)
            if result.returnCode == 0:
                Colored.PrintSuccess(f"Linux deploy copied to {target}")
                return 0
            return 1

        # Local copy to destination directory.
        dst_dir = Path(target).expanduser().resolve()
        FileSystem.MakeDirectory(dst_dir)
        dst = dst_dir / exe_path.name
        shutil.copy2(exe_path, dst)
        Colored.PrintSuccess(f"Linux deploy copied to {dst}")
        return 0

    @staticmethod
    def _DeployMacOS(workspace, project, parsed):
        """DÃ©ploiement sur macOS (copie locale)."""
        from .build import BuildCommand
        build_args = ["--config", parsed.config, "--action", "deploy", "--platform", "macOS", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1
        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, "macOS", project.name, parsed.verbose,
            action="deploy",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform="macOS",
                target=project.name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=["action:deploy", "deploy:macos"]
            )
        )
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
        """DÃ©ploiement sur Windows (copie locale)."""
        from .build import BuildCommand
        build_args = ["--config", parsed.config, "--action", "deploy", "--platform", "Windows", "--target", project.name]
        if parsed.jenga_file:
            build_args += ["--jenga-file", parsed.jenga_file]
        if BuildCommand.Execute(build_args) != 0:
            return 1
        builder = BuildCommand.CreateBuilder(
            workspace, parsed.config, "Windows", project.name, parsed.verbose,
            action="deploy",
            options=BuildCommand.CollectFilterOptions(
                config=parsed.config,
                platform="Windows",
                target=project.name,
                verbose=parsed.verbose,
                no_cache=False,
                no_daemon=parsed.no_daemon,
                extra=["action:deploy", "deploy:windows"]
            )
        )
        exe_path = builder.GetTargetPath(project)
        if exe_path.exists():
            Colored.PrintInfo(f"Executable built at: {exe_path}")
        return 0    

