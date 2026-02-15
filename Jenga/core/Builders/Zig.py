#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zig Builder - Cross-compilation using Zig as a drop-in C/C++ compiler.
Supports cross-compilation to Linux, Windows, macOS without external toolchains.
"""

from pathlib import Path
from typing import List
import shlex

from Jenga.Core.Api import Project, ProjectKind
from ...Utils import Process, FileSystem
from ..Builder import Builder


class ZigBuilder(Builder):
    """
    Builder for cross-compilation using Zig.
    Zig uses different command syntax: zig c++ / zig cc instead of traditional flags.
    """

    def GetObjectExtension(self) -> str:
        return ".o"

    @staticmethod
    def _EnumValue(v):
        return v.value if hasattr(v, "value") else v

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        if project.kind == ProjectKind.SHARED_LIB:
            target_os = self._EnumValue(project.targetOs or self.workspace.targetOs)
            if target_os == "WINDOWS":
                return ".dll"
            elif target_os == "MACOS":
                return ".dylib"
            return ".so"
        # Executable
        target_os = self._EnumValue(project.targetOs or self.workspace.targetOs)
        if target_os == "WINDOWS":
            return ".exe"
        return ""

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        # Zig command structure: zig c++ [args] -c source.cpp -o output.o
        zig_exe = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath

        # Extract base zig.exe path (remove "c++" or "cc" from flags if present)
        zig_base = str(zig_exe)

        # Build command: zig c++ -target <triple> -c -o output.o source.cpp
        lang_cmd = "c++" if project.language.value in ("C++", "Objective-C++") else "cc"

        args = [zig_base, lang_cmd]

        # Target triple
        if self.toolchain.targetTriple:
            args.extend(["-target", self.toolchain.targetTriple])

        args.extend(["-c"])  # Compile only
        args.append(str(src))  # Source file
        args.extend(["-o", str(obj)])  # Output file

        # Add compiler flags
        args.extend(self._GetCompilerFlags(project))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            # Use zig ar for static libraries
            zig_exe = str(self.toolchain.arPath or self.toolchain.cxxPath)
            args = [zig_exe, "ar", "rcs", str(out)]
            args.extend(objectFiles)
            result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
            return result.returnCode == 0

        # Linking: zig c++ -target <triple> obj1.o obj2.o -o output
        zig_exe = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        zig_base = str(zig_exe)

        lang_cmd = "c++" if project.language.value in ("C++", "Objective-C++") else "cc"

        args = [zig_base, lang_cmd]

        # Target triple
        if self.toolchain.targetTriple:
            args.extend(["-target", self.toolchain.targetTriple])

        # Object files
        args.extend(objectFiles)

        # Output file
        args.extend(["-o", str(out)])

        # Linker flags
        args.extend(self._GetLinkerFlags(project))

        # Library directories
        for libdir in project.libDirs:
            args.append(f"-L{self.ResolveProjectPath(project, libdir)}")

        # Libraries
        for lib in project.links:
            if self._IsDirectLibPath(lib):
                args.append(self.ResolveProjectPath(project, lib))
            else:
                args.append(f"-l{lib}")

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        p = Path(lib)
        return p.suffix in (".a", ".lib", ".so", ".dylib", ".dll") or "/" in lib or "\\" in lib or p.is_absolute()

    def _GetCompilerFlags(self, project: Project) -> List[str]:
        flags = []

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{self.ResolveProjectPath(project, inc)}")

        # Defines
        for define in self.toolchain.defines:
            flags.append(f"-D{define}")
        for define in project.defines:
            flags.append(f"-D{define}")

        # Debug
        if project.symbols:
            flags.append("-g")

        # Optimization
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
        elif warn == "Error":
            flags.append("-Werror")

        # C++ standard
        if project.language.value == "C++":
            # Zig uses -std=c++17 format
            std = project.cppdialect.lower().replace("c", "C")  # c++17 -> C++17
            flags.append(f"-std={std}")
        else:
            flags.append(f"-std={project.cdialect.lower()}")

        # Custom cflags/cxxflags from project
        if project.language.value == "C++":
            flags.extend(project.cxxflags)
        else:
            flags.extend(project.cflags)

        return flags

    def _GetLinkerFlags(self, project: Project) -> List[str]:
        flags = []

        # Project linker flags
        for f in project.ldflags:
            if isinstance(f, str):
                flags.extend(shlex.split(f))
            else:
                flags.append(str(f))

        # Toolchain linker flags (skip "c++" command if present in ldflags)
        for f in self.toolchain.ldflags:
            if f in ["c++", "cc"]:  # Skip command names
                continue
            if isinstance(f, str):
                flags.extend(shlex.split(f))
            else:
                flags.append(str(f))

        return flags
