#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS Builder – Compilation pour macOS (Mach-O).
Supporte Apple Clang.
Gère les .dylib, .a, .app bundles, frameworks.
"""

from pathlib import Path
from typing import List
import plistlib

from Jenga.Core.Api import Project, ProjectKind, CompilerFamily, TargetArch
from ...Utils import Process, FileSystem
from ..Builder import Builder


class MacOSBuilder(Builder):
    """
    Builder pour macOS.
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)
        # Apple Clang ou Clang standard
        self.is_apple_clang = self.toolchain.compilerFamily == CompilerFamily.APPLE_CLANG

    @staticmethod
    def _EnumValue(v):
        return v.value if hasattr(v, "value") else v

    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        elif project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            return ""  # exécutable Unix
        else:
            return ""

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [compiler, "-c", "-o", str(obj)]
        args.extend(self.GetDependencyFlags(str(obj)))
        args.extend(self._GetCompilerFlags(project))
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def GetModuleFlags(self, sourceFile: str) -> List[str]:
        return ["-std=c++20", "-fmodules", "-fcxx-modules"]

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            ar = self.toolchain.arPath or "ar"
            args = [ar, "rcs", str(out)]
            args.extend(self.toolchain.arflags)
            args.extend(objectFiles)
        else:
            linker = self.toolchain.cxxPath
            args = [linker, "-o", str(out)]
            if project.kind == ProjectKind.SHARED_LIB:
                args.append("-dynamiclib")
            # Frameworks
            for fw in getattr(self.toolchain, 'frameworks', []):
                args.append(f"-framework {fw}")
            for fw_path in getattr(self.toolchain, 'frameworkPaths', []):
                args.append(f"-F{fw_path}")
            # Bibliothèques
            for libdir in project.libDirs:
                args.append(f"-L{self.ResolveProjectPath(project, libdir)}")
            for lib in project.links:
                args.append(f"-l{lib}")
            # RPATH
            args.append("-Wl,-rpath,@loader_path")
            args.extend(self.toolchain.ldflags)
            args.extend(objectFiles)

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def _GetCompilerFlags(self, project: Project) -> List[str]:
        flags = []

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{self.ResolveProjectPath(project, inc)}")

        # Définitions
        for define in self.toolchain.defines:
            flags.append(f"-D{define}")
        for define in project.defines:
            flags.append(f"-D{define}")

        # Debug
        if project.symbols:
            flags.append("-g")

        # Optimisation
        opt = self._EnumValue(project.optimize)
        if opt == "Off":
            flags.append("-O0")
        elif opt == "Size":
            flags.append("-Os")
        elif opt == "Speed":
            flags.append("-O2")
        elif opt == "Full":
            flags.append("-O3")

        # Warnings
        warn = self._EnumValue(project.warnings)
        if warn == "All":
            flags.append("-Wall")
        elif warn == "Extra":
            flags.append("-Wextra")
        elif warn == "Pedantic":
            flags.append("-pedantic")
        elif warn == "Everything" and self.is_apple_clang:
            flags.append("-Weverything")
        elif warn == "Error":
            flags.append("-Werror")

        # Standard
        if project.language.value in ("C++", "Objective-C++"):
            if project.cppdialect:
                flags.append(f"-std={project.cppdialect.lower()}")
            flags.extend(self.toolchain.cxxflags)
        else:
            if project.cdialect:
                flags.append(f"-std={project.cdialect.lower()}")
            flags.extend(self.toolchain.cflags)

        # Objective-C
        if project.language.value in ("Objective-C", "Objective-C++"):
            flags.append("-ObjC")

        # Position Independent Code
        if project.kind == ProjectKind.SHARED_LIB:
            flags.append("-fPIC")

        # Architecture
        if self.targetArch == TargetArch.ARM64:
            flags.append("-arch arm64")
        elif self.targetArch == TargetArch.X86_64:
            flags.append("-arch x86_64")

        return flags
