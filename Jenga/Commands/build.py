#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build command – Compile le workspace ou un projet spécifique.
Utilise le daemon s'il est actif, sinon exécute un build direct.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ..Core.Builder import Builder
from ..Core.Platform import Platform
from ..Core.Cache import Cache
from ..Core.Loader import Loader
from ..Core.State import BuildState
from ..Utils import Colored, Reporter, FileSystem
from ..Core import Api


class BuildCommand:
    """jenga build [--config NAME] [--platform NAME] [--target PROJECT] [--no-cache] [--verbose]"""

    @staticmethod
    def CreateBuilder(workspace, config: str, platform: str, target: Optional[str], verbose: bool) -> Builder:
        """Crée un builder pour la configuration et la plateforme spécifiées."""
        # Déterminer la cible à partir de la plateforme
        target_os = None
        target_arch = None
        target_env = None

        if platform:
            parts = platform.split('-')
            os_name = parts[0]
            for os_enum in Api.TargetOS:
                if os_enum.value.lower() == os_name.lower():
                    target_os = os_enum
                    break
            if len(parts) > 1:
                arch_name = parts[1]
                for arch_enum in Api.TargetArch:
                    if arch_enum.value.lower() == arch_name.lower():
                        target_arch = arch_enum
                        break
            if len(parts) > 2:
                env_name = parts[2]
                for env_enum in Api.TargetEnv:
                    if env_enum.value.lower() == env_name.lower():
                        target_env = env_enum
                        break

        # Valeurs par défaut
        if target_os is None:
            if workspace.targetOses:
                host_os = Platform.GetHostOS()
                target_os = host_os if host_os in workspace.targetOses else workspace.targetOses[0]
            else:
                target_os = Platform.GetHostOS()
        if target_arch is None:
            if workspace.targetArchs:
                host_arch = Platform.GetHostArchitecture()
                target_arch = host_arch if host_arch in workspace.targetArchs else workspace.targetArchs[0]
            else:
                target_arch = Platform.GetHostArchitecture()
        # Leave env unspecified unless explicitly requested in --platform.
        # This lets resolver prefer the best matching toolchain (e.g. mingw clang++).
        if target_env is None:
            target_env = None

        # Utiliser le système de résolution des builders
        from ..Core.Builders import get_builder_class
        builder_class = get_builder_class(target_os.value)
        if not builder_class:
            raise RuntimeError(f"Unsupported target platform: {target_os.value}")

        return builder_class(
            workspace=workspace,
            config=config,
            platform=platform,
            targetOs=target_os,
            targetArch=target_arch,
            targetEnv=target_env,
            verbose=verbose
        )

    @staticmethod
    def Execute(args: List[str]) -> int:

        parser = argparse.ArgumentParser(prog="jenga build", description="Build the workspace or a specific project.")
        parser.add_argument("--config", default="Debug", help="Build configuration (Debug, Release, etc.)")
        parser.add_argument("--platform", default=None, help="Target platform (Windows, Linux, Android-arm64, etc.)")
        parser.add_argument("--target", default=None, help="Specific project to build")
        parser.add_argument("--no-cache", action="store_true", help="Ignore cache and reload workspace")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--no-daemon", action="store_true", help="Do not use daemon even if available")
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

        # Essayer d'utiliser le daemon si disponible
        if not parsed.no_daemon:
            from ..Core.Daemon import DaemonClient, Daemon
            client = DaemonClient(workspace_root)
            if client.IsAvailable():
                Colored.PrintInfo("Using build daemon...")
                try:
                    response = client.SendCommand('build', {
                        'config': parsed.config,
                        'platform': parsed.platform,
                        'target': parsed.target,
                        'verbose': parsed.verbose
                    })
                    if response.get('status') == 'ok':
                        return response.get('return_code', 0)
                    else:
                        Colored.PrintError(f"Daemon build failed: {response.get('message')}")
                        return 1
                except Exception as e:
                    Colored.PrintWarning(f"Daemon communication failed: {e}. Falling back to direct build.")

        # Direct build (sans daemon)
        # 1. Charger le workspace (avec cache si non --no-cache)
        loader = Loader(verbose=parsed.verbose)
        cache = Cache(workspace_root)

        if parsed.no_cache:
            cache.Invalidate()
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace:
                cache.SaveWorkspace(workspace, entry_file, loader)
        else:
            workspace = cache.LoadWorkspace(entry_file, loader)
            if workspace is None:
                Colored.PrintInfo("Loading workspace...")
                workspace = loader.LoadWorkspace(str(entry_file))
                if workspace:
                    cache.SaveWorkspace(workspace, entry_file, loader)

        if workspace is None:
            Colored.PrintError("Failed to load workspace.")
            return 1
        # 2. Créer le builder
        try:
            builder = BuildCommand.CreateBuilder(
                workspace,
                config=parsed.config,
                platform=parsed.platform,
                target=parsed.target,
                verbose=parsed.verbose
            )
        except Exception as e:
            Colored.PrintError(f"Cannot create builder: {e}")
            return 1

        # 3. Exécuter le build
        return builder.Build(parsed.target)
