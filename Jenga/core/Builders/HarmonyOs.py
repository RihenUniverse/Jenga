#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HarmonyOS Builder – Compilation pour HarmonyOS / OpenHarmony.
Utilise le SDK HarmonyOS (hdc, hvigor, etc.) avec le NDK HarmonyOS.
"""

import os, sys
from pathlib import Path
from typing import List, Optional

from Jenga.Core.Api import Project, ProjectKind, TargetArch, TargetOS, TargetEnv, CompilerFamily
from ...Utils import Process, FileSystem, Colored
from ..Builder import Builder
from ..Platform import Platform
from ..Toolchains import ToolchainManager


class HarmonyOsBuilder(Builder):
    """
    Builder pour HarmonyOS.
    Supporte les architectures : arm64-v8a, armeabi-v7a, x86_64.
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)
        self.sdk_path = self._ResolveHarmonySDK()
        self.ndk_path = self._ResolveHarmonyNDK()
        self._PrepareToolchain()

    def _ResolveHarmonySDK(self) -> Optional[Path]:
        """Trouve le SDK HarmonyOS."""
        # 1. Variable d'environnement
        if "HARMONY_OS_SDK" in os.environ:
            return Path(os.environ["HARMONY_OS_SDK"])
        # 2. Workspace
        if hasattr(self.workspace, 'harmonySdkPath') and self.workspace.harmonySdkPath:
            return Path(self.workspace.harmonySdkPath)
        # 3. Chemins par défaut
        if sys.platform == "win32":
            candidates = [Path("C:/Program Files/HarmonyOS/SDK")]
        elif sys.platform == "darwin":
            candidates = [Path("/Applications/HarmonyOS/SDK")]
        else:
            candidates = [Path("/opt/harmonyos/sdk")]
        for cand in candidates:
            if cand.exists():
                return cand
        return None

    def _ResolveHarmonyNDK(self) -> Optional[Path]:
        """Trouve le NDK HarmonyOS (dans le SDK)."""
        if not self.sdk_path:
            return None
        # Le NDK se trouve dans sdk/openharmony/{version}/native
        native_dirs = list(self.sdk_path.glob("openharmony/*/native"))
        if native_dirs:
            return native_dirs[0]
        return None

    def _PrepareToolchain(self):
        """Configure la toolchain HarmonyOS."""
        if not self.ndk_path:
            raise RuntimeError("HarmonyOS NDK not found. Please set HARMONY_OS_SDK.")

        # Utiliser la toolchain LLVM du NDK
        llvm_dir = self.ndk_path / "llvm"
        if not llvm_dir.exists():
            # Essayer build-tools/cmake/...
            build_tools = self.ndk_path / "build-tools" / "cmake"
            if build_tools.exists():
                llvm_dir = build_tools / "bin"  # contient clang
            else:
                raise RuntimeError(f"LLVM toolchain not found in NDK: {self.ndk_path}")

        arch_map = {
            TargetArch.ARM: "arm-linux-ohos",
            TargetArch.ARM64: "aarch64-linux-ohos",
            TargetArch.X86_64: "x86_64-linux-ohos",
        }
        triple = arch_map.get(self.targetArch, "aarch64-linux-ohos")

        # Créer ou mettre à jour la toolchain
        if self.toolchain:
            self.toolchain.ccPath = str(llvm_dir / "bin" / "clang")
            self.toolchain.cxxPath = str(llvm_dir / "bin" / "clang++")
            self.toolchain.arPath = str(llvm_dir / "bin" / "llvm-ar")
            self.toolchain.ldPath = str(llvm_dir / "bin" / "ld")
            self.toolchain.stripPath = str(llvm_dir / "bin" / "llvm-strip")
            self.toolchain.targetTriple = triple
            self.toolchain.sysroot = str(self.ndk_path / "sysroot")

    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".so"
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        else:
            return ""  # exécutable (pas d'extension)

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [compiler, "-c", "-o", str(obj)]
        args.extend(self._GetCompilerFlags(project))
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            ar = self.toolchain.arPath or "llvm-ar"
            args = [ar, "rcs", str(out)] + objectFiles
        else:
            linker = self.toolchain.cxxPath
            args = [linker, "-o", str(out)]
            args.extend(self._GetLinkerFlags(project))
            for libdir in project.libDirs:
                args.append(f"-L{libdir}")
            for lib in project.links:
                args.append(f"-l{lib}")
            args.extend(objectFiles)

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def _GetCompilerFlags(self, project: Project) -> List[str]:
        flags = []

        # Target triple et sysroot
        flags.append(f"--target={self.toolchain.targetTriple}")
        if self.toolchain.sysroot:
            flags.append(f"--sysroot={self.toolchain.sysroot}")

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{inc}")

        # Définitions
        for define in project.defines:
            flags.append(f"-D{define}")
        flags.append("-D__OHOS__")

        # Debug/optimisation
        if project.symbols:
            flags.append("-g")
        opt = project.optimize.value if hasattr(project.optimize, 'value') else project.optimize
        if opt == "Off":
            flags.append("-O0")
        elif opt == "Size":
            flags.append("-Os")
        elif opt == "Speed":
            flags.append("-O2")
        elif opt == "Full":
            flags.append("-O3")

        # Warnings
        warn = project.warnings.value if hasattr(project.warnings, 'value') else project.warnings
        if warn == "All":
            flags.append("-Wall")
        elif warn == "Extra":
            flags.append("-Wextra")
        elif warn == "Error":
            flags.append("-Werror")

        # Standard
        if project.language.value == "C++":
            flags.append(f"-std={project.cppdialect.lower()}")
        else:
            flags.append(f"-std={project.cdialect.lower()}")

        # PIC
        flags.append("-fPIC")

        return flags

    def _GetLinkerFlags(self, project: Project) -> List[str]:
        flags = []
        flags.append(f"--target={self.toolchain.targetTriple}")
        if self.toolchain.sysroot:
            flags.append(f"--sysroot={self.toolchain.sysroot}")
        flags.append("-llog")
        flags.append("-lhilog")  # HarmonyOS logging
        flags.append("-lohos")   # HarmonyOS base
        return flags