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
    ALL_PLATFORMS_TOKEN = "jengaall"

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
    def IsAllPlatformsRequest(platform: Optional[str]) -> bool:
        """True si --platform jengaall a été demandé."""
        return bool(platform) and platform.strip().lower() == BuildCommand.ALL_PLATFORMS_TOKEN

    @staticmethod
    def GetAllDeclaredPlatforms(workspace) -> List[str]:
        """
        Génère la liste des plateformes à construire pour jengaall
        à partir des target OS et architectures déclarés.
        """
        oses = workspace.targetOses or [Platform.GetHostOS()]
        archs = workspace.targetArchs or [Platform.GetHostArchitecture()]

        platforms: List[str] = []
        for os_enum in oses:
            os_name = os_enum.value if hasattr(os_enum, "value") else str(os_enum)
            for arch_enum in archs:
                arch_name = arch_enum.value if hasattr(arch_enum, "value") else str(arch_enum)
                platform_name = f"{os_name}-{arch_name}" if arch_name else os_name
                if platform_name not in platforms:
                    platforms.append(platform_name)
        return platforms

    @staticmethod
    def BuildAcrossPlatforms(workspace, config: str, platforms: List[str],
                             target: Optional[str], verbose: bool) -> int:
        """
        Build séquentiel sur plusieurs plateformes.
        Continue même si une plateforme échoue, puis renvoie un code global.
        """
        if not platforms:
            Colored.PrintError("No platform available for --platform jengaall.")
            return 1

        Colored.PrintInfo(f"Building across {len(platforms)} platform(s): {', '.join(platforms)}")
        failures = 0

        for idx, platform_name in enumerate(platforms, start=1):
            Colored.PrintInfo(f"\n[{idx}/{len(platforms)}] Building platform: {platform_name}")
            try:
                builder = BuildCommand.CreateBuilder(
                    workspace,
                    config=config,
                    platform=platform_name,
                    target=target,
                    verbose=verbose
                )
            except Exception as e:
                failures += 1
                Colored.PrintError(f"[{platform_name}] Cannot create builder: {e}")
                continue

            ret = builder.Build(target)
            if ret != 0:
                failures += 1
                Colored.PrintError(f"[{platform_name}] Build failed.")
            else:
                Colored.PrintSuccess(f"[{platform_name}] Build succeeded.")

        if failures:
            Colored.PrintError(f"Multi-platform build finished with {failures} failure(s).")
            return 1

        Colored.PrintSuccess("Multi-platform build succeeded.")
        return 0

    @staticmethod
    def Execute(args: List[str]) -> int:

        parser = argparse.ArgumentParser(prog="jenga build", description="Build the workspace or a specific project.")
        parser.add_argument("--config", default="Debug", help="Build configuration (Debug, Release, etc.)")
        parser.add_argument("--platform", default=None, help="Target platform (Windows, Linux, Android-arm64, etc.) or 'jengaall'")
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

        if BuildCommand.IsAllPlatformsRequest(parsed.platform):
            # Multi-platform orchestration is done in direct mode from CLI.
            parsed.no_daemon = True

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

        loaded_from_cache = False

        if parsed.no_cache:
            cache.Invalidate()
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace:
                cache.SaveWorkspace(workspace, entry_file, loader)
        else:
            workspace = cache.LoadWorkspace(entry_file, loader)
            loaded_from_cache = workspace is not None
            if workspace is None:
                Colored.PrintInfo("Loading workspace...")
                workspace = loader.LoadWorkspace(str(entry_file))
                if workspace:
                    cache.SaveWorkspace(workspace, entry_file, loader)

        if workspace is None:
            Colored.PrintError("Failed to load workspace.")
            return 1

        if BuildCommand.IsAllPlatformsRequest(parsed.platform):
            platforms = BuildCommand.GetAllDeclaredPlatforms(workspace)
            return BuildCommand.BuildAcrossPlatforms(
                workspace,
                config=parsed.config,
                platforms=platforms,
                target=parsed.target,
                verbose=parsed.verbose
            )

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
        result = builder.Build(parsed.target)

        # Fallback robuste: si le build échoue avec un cache "no changes",
        # on force un rechargement complet une seule fois.
        if (
            result != 0
            and not parsed.no_cache
            and loaded_from_cache
            and getattr(workspace, "_cache_status", "") == "no_changes"
        ):
            Colored.PrintWarning("Build failed with cached workspace. Retrying once with fresh workspace...")
            cache.Invalidate()
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace is None:
                return result
            cache.SaveWorkspace(workspace, entry_file, loader)

            try:
                builder = BuildCommand.CreateBuilder(
                    workspace,
                    config=parsed.config,
                    platform=parsed.platform,
                    target=parsed.target,
                    verbose=parsed.verbose
                )
            except Exception as e:
                Colored.PrintError(f"Cannot create builder after cache refresh: {e}")
                return result

            return builder.Build(parsed.target)

        return result
