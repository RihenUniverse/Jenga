#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Platform – Détection de la plateforme hôte et gestion des cibles.
Fournit des informations sur l'OS, l'architecture, l'environnement.
Supporte la cross‑compilation via la notion de cible explicite.
"""

import os
import sys
import platform
from enum import Enum
from typing import Dict, Optional, Tuple, List, Any

from Jenga.Core.Api import TargetOS, TargetArch, TargetEnv, CompilerFamily


class Platform:
    """
    Détection et normalisation des plateformes.
    Méthodes statiques uniquement.
    """

    _host_os: Optional[TargetOS] = None
    _host_arch: Optional[TargetArch] = None
    _host_env: Optional[TargetEnv] = None
    _host_triple: Optional[str] = None

    @classmethod
    def GetHostOS(cls) -> TargetOS:
        """Retourne l'OS de la machine hôte."""
        if cls._host_os is None:
            system = platform.system().lower()
            if system == "windows":
                cls._host_os = TargetOS.WINDOWS
            elif system == "linux":
                cls._host_os = TargetOS.LINUX
            elif system == "darwin":
                cls._host_os = TargetOS.MACOS
            elif "bsd" in system:
                cls._host_os = TargetOS.FREEBSD
            else:
                cls._host_os = TargetOS.LINUX  # fallback
        return cls._host_os

    @classmethod
    def GetHostArchitecture(cls) -> TargetArch:
        """Retourne l'architecture de la machine hôte."""
        if cls._host_arch is None:
            machine = platform.machine().lower()
            if machine in ("x86_64", "amd64", "x64"):
                cls._host_arch = TargetArch.X86_64
            elif machine in ("i386", "i686", "x86"):
                cls._host_arch = TargetArch.X86
            elif machine in ("arm64", "aarch64"):
                cls._host_arch = TargetArch.ARM64
            elif machine.startswith("arm"):
                cls._host_arch = TargetArch.ARM
            elif machine in ("ppc64le", "ppc64"):
                cls._host_arch = TargetArch.POWERPC64
            elif machine == "ppc":
                cls._host_arch = TargetArch.POWERPC
            elif machine in ("mips", "mipsel"):
                cls._host_arch = TargetArch.MIPS
            elif machine in ("mips64", "mips64el"):
                cls._host_arch = TargetArch.MIPS64
            else:
                cls._host_arch = TargetArch.X86_64  # fallback
        return cls._host_arch

    @classmethod
    def GetHostEnvironment(cls) -> TargetEnv:
        """Retourne l'environnement C par défaut (glibc, msvc, musl, etc.)."""
        if cls._host_env is None:
            if cls.GetHostOS() == TargetOS.WINDOWS:
                cls._host_env = TargetEnv.MSVC
            elif cls.GetHostOS() == TargetOS.LINUX:
                # Détection naïve : si on est sur Alpine, musl, sinon glibc
                try:
                    with open("/etc/alpine-release") as f:
                        cls._host_env = TargetEnv.MUSL
                except:
                    cls._host_env = TargetEnv.GNU
            elif cls.GetHostOS() == TargetOS.MACOS:
                cls._host_env = TargetEnv.IOS  # ou spécifique ? Utilisons GNU par défaut
                cls._host_env = TargetEnv.GNU
            else:
                cls._host_env = TargetEnv.GNU
        return cls._host_env

    @classmethod
    def GetHostTriple(cls) -> str:
        """Retourne le triplet canonique (ex: x86_64-pc-linux-gnu)."""
        if cls._host_triple is None:
            os_part = {
                TargetOS.WINDOWS: "windows",
                TargetOS.LINUX: "linux",
                TargetOS.MACOS: "darwin",
                TargetOS.FREEBSD: "freebsd",
            }.get(cls.GetHostOS(), "unknown")
            arch_part = {
                TargetArch.X86: "i686",
                TargetArch.X86_64: "x86_64",
                TargetArch.ARM: "arm",
                TargetArch.ARM64: "aarch64",
                TargetArch.POWERPC: "powerpc",
                TargetArch.POWERPC64: "powerpc64",
            }.get(cls.GetHostArchitecture(), "unknown")
            vendor = "pc" if os_part in ("windows", "linux") else "apple"
            env_part = {
                TargetEnv.GNU: "gnu",
                TargetEnv.MUSL: "musl",
                TargetEnv.MSVC: "msvc",
                TargetEnv.MINGW: "mingw32",
            }.get(cls.GetHostEnvironment(), "gnu")
            cls._host_triple = f"{arch_part}-{vendor}-{os_part}-{env_part}"
        return cls._host_triple

    @classmethod
    def IsPlatformAvailable(cls, targetOs: TargetOS, targetArch: TargetArch) -> bool:
        """
        Vérifie si une cible est théoriquement supportée par Jenga.
        (Ne vérifie pas la présence des toolchains).
        """
        # Liste des combinaisons supportées
        supported = [
            (TargetOS.WINDOWS, TargetArch.X86),
            (TargetOS.WINDOWS, TargetArch.X86_64),
            (TargetOS.WINDOWS, TargetArch.ARM64),
            (TargetOS.LINUX, TargetArch.X86),
            (TargetOS.LINUX, TargetArch.X86_64),
            (TargetOS.LINUX, TargetArch.ARM),
            (TargetOS.LINUX, TargetArch.ARM64),
            (TargetOS.MACOS, TargetArch.X86_64),
            (TargetOS.MACOS, TargetArch.ARM64),
            (TargetOS.ANDROID, TargetArch.ARM),
            (TargetOS.ANDROID, TargetArch.ARM64),
            (TargetOS.ANDROID, TargetArch.X86),
            (TargetOS.ANDROID, TargetArch.X86_64),
            (TargetOS.IOS, TargetArch.ARM64),
            (TargetOS.IOS, TargetArch.X86_64),  # simulateur
            (TargetOS.TVOS, TargetArch.ARM64),
            (TargetOS.TVOS, TargetArch.X86_64),  # simulateur
            (TargetOS.WATCHOS, TargetArch.ARM64),
            (TargetOS.WATCHOS, TargetArch.X86_64),  # simulateur
            (TargetOS.WEB, TargetArch.WASM32),
            (TargetOS.WEB, TargetArch.WASM64),
            (TargetOS.PS4, TargetArch.X86_64),
            (TargetOS.PS5, TargetArch.X86_64),
            (TargetOS.XBOX_ONE, TargetArch.X86_64),
            (TargetOS.XBOX_SERIES, TargetArch.X86_64),
            (TargetOS.SWITCH, TargetArch.ARM64),
        ]
        return (targetOs, targetArch) in supported

    @classmethod
    def GetDefaultTarget(cls) -> Tuple[TargetOS, TargetArch, TargetEnv]:
        """Cible par défaut = hôte."""
        return cls.GetHostOS(), cls.GetHostArchitecture(), cls.GetHostEnvironment()

    @classmethod
    def ParseTriple(cls, triple: str) -> Dict[str, str]:
        """
        Décompose un triplet en composants.
        Ex: x86_64-pc-linux-gnu -> {'arch': 'x86_64', 'vendor': 'pc', 'os': 'linux', 'env': 'gnu'}
        """
        parts = triple.split('-')
        if len(parts) == 4:
            return {'arch': parts[0], 'vendor': parts[1], 'os': parts[2], 'env': parts[3]}
        elif len(parts) == 3:
            return {'arch': parts[0], 'vendor': 'unknown', 'os': parts[1], 'env': parts[2]}
        elif len(parts) == 2:
            return {'arch': parts[0], 'vendor': 'unknown', 'os': parts[1], 'env': 'unknown'}
        else:
            return {'arch': triple, 'vendor': 'unknown', 'os': 'unknown', 'env': 'unknown'}

    @staticmethod
    def NormalizeTarget(os: Optional[TargetOS] = None,
                        arch: Optional[TargetArch] = None,
                        env: Optional[TargetEnv] = None) -> Tuple[TargetOS, TargetArch, TargetEnv]:
        """Si une valeur est None, utilise celle de l'hôte."""
        if os is None:
            os = Platform.GetHostOS()
        if arch is None:
            arch = Platform.GetHostArchitecture()
        if env is None:
            env = Platform.GetHostEnvironment()
        return os, arch, env
