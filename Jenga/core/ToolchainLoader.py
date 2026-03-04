#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chargeur de toolchains personnalisés depuis ~/.jenga/toolchains/
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .JengaConfig import GetGlobalConfig


class ToolchainLoader:
    """
    Charge les toolchains personnalisés depuis la configuration utilisateur.
    """

    @staticmethod
    def LoadUserToolchains() -> Dict[str, dict]:
        """
        Charge tous les toolchains depuis ~/.jenga/toolchains/

        Returns:
            Dict[str, dict]: Dictionnaire {nom_toolchain: données}
        """
        config = GetGlobalConfig()
        toolchains_dir = config.config_dir / "toolchains"

        if not toolchains_dir.exists():
            return {}

        toolchains = {}
        for toolchain_file in toolchains_dir.glob("*.json"):
            try:
                with open(toolchain_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    toolchains[toolchain_file.stem] = data
            except Exception as e:
                print(f"Warning: Failed to load toolchain {toolchain_file.name}: {e}")

        return toolchains

    @staticmethod
    def RegisterUserToolchainsToAPI():
        """
        Enregistre automatiquement les toolchains utilisateur dans l'API Jenga.
        Doit être appelé depuis un contexte workspace.
        """
        from ..Core.Api import _currentWorkspace, toolchain as toolchain_context
        from ..Core.Api import settarget, ccompiler, cppcompiler, linker, archiver
        from ..Core.Api import cflags, cxxflags, ldflags, arflags, targettriple, sysroot

        if not _currentWorkspace:
            return

        user_toolchains = ToolchainLoader.LoadUserToolchains()

        for name, data in user_toolchains.items():
            # Créer le toolchain
            tc_type = data.get('type', 'gcc')
            target = data.get('target', {})

            with toolchain_context(name, tc_type):
                # Target
                if target:
                    target_os = target.get('os', 'Linux')
                    target_arch = target.get('arch', 'x86_64')
                    target_env = target.get('env', 'gnu')
                    settarget(target_os, target_arch, target_env)

                # Target triple
                if 'target_triple' in data:
                    targettriple(data['target_triple'])

                # Sysroot
                if 'sysroot' in data:
                    sysroot(data['sysroot'])

                # Compilers
                if 'cc' in data:
                    ccompiler(data['cc'])
                if 'cxx' in data:
                    cppcompiler(data['cxx'])
                if 'linker' in data:
                    linker(data['linker'])
                if 'ar' in data:
                    archiver(data['ar'])

                # Flags
                if 'cflags' in data:
                    cflags(data['cflags'])
                if 'cxxflags' in data:
                    cxxflags(data['cxxflags'])
                if 'ldflags' in data:
                    ldflags(data['ldflags'])
                if 'arflags' in data:
                    arflags(data['arflags'])

    @staticmethod
    def GetAvailableToolchains() -> List[str]:
        """
        Retourne la liste de tous les toolchains disponibles (globaux + utilisateur).
        """
        # Toolchains globaux depuis GlobalToolchains
        try:
            from ..GlobalToolchains import RegisterJengaGlobalToolchains
            # TODO: Extraire la liste des toolchains globaux
            global_toolchains = [
                "android-ndk",
                "clang-cl",
                "clang-cross-linux",
                "clang-mingw",
                "emscripten",
                "host-apple-clang",
                "host-clang",
                "host-gcc",
                "mingw",
                "msvc",
                "zig-android-arm64",
                "zig-linux-x64",
                "zig-linux-x86_64",
                "zig-macos-arm64",
                "zig-macos-x86_64",
                "zig-web-wasm32",
                "zig-windows-x64",
                "zig-windows-x86_64",
            ]
        except:
            global_toolchains = []

        # Toolchains utilisateur
        user_toolchains = list(ToolchainLoader.LoadUserToolchains().keys())

        return sorted(set(global_toolchains + user_toolchains))


def LoadUserToolchains():
    """Fonction helper pour charger les toolchains utilisateur."""
    return ToolchainLoader.LoadUserToolchains()


def RegisterAllToolchains():
    """Enregistre tous les toolchains (globaux + utilisateur)."""
    # Importer et enregistrer les toolchains globaux
    try:
        from ..GlobalToolchains import RegisterJengaGlobalToolchains
        RegisterJengaGlobalToolchains()
    except Exception as e:
        print(f"Warning: Failed to load global toolchains: {e}")

    # Enregistrer les toolchains utilisateur
    try:
        ToolchainLoader.RegisterUserToolchainsToAPI()
    except Exception as e:
        print(f"Warning: Failed to load user toolchains: {e}")
