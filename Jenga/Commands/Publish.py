#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publish command – Publie des packages sur des registres (NuGet, vcpkg, Conan, npm, etc.)
"""

import argparse
import sys
from pathlib import Path
from typing import List

from ..Utils import Colored, Display, FileSystem, Process


class PublishCommand:
    """jenga publish --registry TYPE [--package PATH] [--version VER] [--api-key KEY]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga publish", description="Publish packages to registries.")
        parser.add_argument("--registry", required=True, choices=['nuget', 'vcpkg', 'conan', 'npm', 'pypi', 'custom'],
                            help="Registry type")
        parser.add_argument("--package", help="Path to package file (or directory)")
        parser.add_argument("--version", help="Package version")
        parser.add_argument("--api-key", help="API key for registry")
        parser.add_argument("--repo", help="Repository URL (if custom)")
        parser.add_argument("--dry-run", action="store_true", help="Simulate publishing")
        parser.add_argument("--verbose", "-v", action="store_true")
        parsed = parser.parse_args(args)

        # Ici on pourrait charger le workspace pour récupérer les infos de projet
        # Mais pour l'instant on garde simple

        if parsed.registry == 'nuget':
            return PublishCommand._PublishNuGet(parsed)
        elif parsed.registry == 'vcpkg':
            return PublishCommand._PublishVcpkg(parsed)
        elif parsed.registry == 'conan':
            return PublishCommand._PublishConan(parsed)
        elif parsed.registry == 'npm':
            return PublishCommand._PublishNpm(parsed)
        elif parsed.registry == 'pypi':
            return PublishCommand._PublishPyPi(parsed)
        elif parsed.registry == 'custom':
            return PublishCommand._PublishCustom(parsed)
        return 1

    @staticmethod
    def _PublishNuGet(parsed):
        """Publie un package .nupkg sur nuget.org ou serveur privé."""
        package_path = parsed.package or "<package.nupkg>"
        nuget = FileSystem.FindExecutable("nuget") or FileSystem.FindExecutable("dotnet")
        cmd = []
        if nuget and "dotnet" in nuget:
            cmd = ["dotnet", "nuget", "push", package_path]
        else:
            cmd = ["nuget", "push", package_path]
        if parsed.api_key:
            cmd += ["-ApiKey", parsed.api_key]
        if parsed.repo:
            cmd += ["-Source", parsed.repo]
        if parsed.dry_run:
            Colored.PrintInfo(f"[DRY RUN] {' '.join(cmd)}")
            return 0
        if not parsed.package:
            Colored.PrintError("--package required for NuGet.")
            return 1
        if not nuget:
            Colored.PrintError("NuGet or dotnet not found.")
            return 1
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return 0 if result.returnCode == 0 else 1

    @staticmethod
    def _PublishVcpkg(parsed):
        if parsed.dry_run:
            Colored.PrintInfo("[DRY RUN] vcpkg publish <package>")
            return 0
        Colored.PrintWarning("vcpkg publishing not yet implemented.")
        return 1

    @staticmethod
    def _PublishConan(parsed):
        if parsed.dry_run:
            Colored.PrintInfo("[DRY RUN] conan upload <package>")
            return 0
        Colored.PrintWarning("Conan publishing not yet implemented.")
        return 1

    @staticmethod
    def _PublishNpm(parsed):
        if parsed.dry_run:
            Colored.PrintInfo("[DRY RUN] npm publish <package>")
            return 0
        Colored.PrintWarning("npm publishing not yet implemented.")
        return 1

    @staticmethod
    def _PublishPyPi(parsed):
        if parsed.dry_run:
            Colored.PrintInfo("[DRY RUN] twine upload <package>")
            return 0
        Colored.PrintWarning("PyPI publishing not yet implemented.")
        return 1

    @staticmethod
    def _PublishCustom(parsed):
        if parsed.dry_run:
            target = parsed.repo or "<custom-registry>"
            Colored.PrintInfo(f"[DRY RUN] custom publish to {target}")
            return 0
        Colored.PrintWarning("Custom registry publishing not yet implemented.")
        return 1
