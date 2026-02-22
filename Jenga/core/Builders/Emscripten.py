#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emscripten Builder – Compilation WebAssembly.
Génère .wasm, .js, .html.
"""

from pathlib import Path
from typing import List
import shlex

from Jenga.Core.Api import Project, ProjectKind
from ...Utils import Process, FileSystem
from ..Builder import Builder


class EmscriptenBuilder(Builder):
    """
    Builder pour WebAssembly via Emscripten.
    """

    def GetObjectExtension(self) -> str:
        return ".o"

    @staticmethod
    def _EnumValue(v):
        return v.value if hasattr(v, "value") else v

    def PreparePCH(self, project: Project, objDir: Path) -> bool:
        project._jengaPchFile = ""
        project._jengaPchHeaderResolved = ""
        project._jengaPchSourceResolved = ""
        if not project.pchHeader:
            return True
        header = Path(self.ResolveProjectPath(project, project.pchHeader))
        if not header.exists():
            return False
        pch_path = objDir / f"{project.name}.pch"
        compiler = self.toolchain.cxxPath or self.toolchain.ccPath
        args = [compiler, "-x", "c++-header", str(header), "-o", str(pch_path)]
        pch_flags = []
        skip_next = False
        for f in self._GetCompilerFlags(project):
            if skip_next:
                skip_next = False
                continue
            if f == "-include-pch":
                skip_next = True
                continue
            pch_flags.append(f)
        args.extend(pch_flags)
        result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
        if result.returnCode != 0:
            return False
        project._jengaPchFile = str(pch_path)
        project._jengaPchHeaderResolved = str(header)
        if project.pchSource:
            project._jengaPchSourceResolved = self.ResolveProjectPath(project, project.pchSource)
        return True

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        if project.kind == ProjectKind.SHARED_LIB:
            return ".wasm"
        # For apps, emit launcher html (which references .js and .wasm).
        return ".html"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [compiler, "-c", "-o", str(obj)]
        args.extend(self.GetDependencyFlags(str(obj)))
        args.extend(self._GetCompilerFlags(project))
        args.extend(self.GetModuleFlags(project, sourceFile))
        args.append(str(src))

        # Sur Windows, les fichiers .bat nécessitent shell=True
        use_shell = compiler and (str(compiler).endswith('.bat') or str(compiler).endswith('.cmd'))
        result = Process.ExecuteCommand(args, captureOutput=True, silent=False, shell=use_shell)
        self._lastResult = result
        return result.returnCode == 0

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        flags = []
        if not self.IsModuleFile(sourceFile):
            return flags
        flags.extend(["-fmodules", "-fbuiltin-module-map", "-std=c++20"])
        obj_dir = self.GetObjectDir(project)
        pcm_name = Path(sourceFile).with_suffix('.pcm').name
        pcm_path = obj_dir / pcm_name
        flags.append(f"-o{str(pcm_path)}")
        return flags

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            ar = self.toolchain.arPath or "emar"
            args = [ar, "rcs", str(out)]
            args.extend(objectFiles)
            # Sur Windows, les fichiers .bat nécessitent shell=True
            use_shell = ar and (str(ar).endswith('.bat') or str(ar).endswith('.cmd'))
            result = Process.ExecuteCommand(args, captureOutput=True, silent=False, shell=use_shell)
            self._lastResult = result
            return result.returnCode == 0

        linker = self.toolchain.cxxPath or self.toolchain.ccPath
        args = [linker, "-o", str(out)]
        args.extend(self._GetLinkerFlags(project))
        # Object files first; static archives are order-sensitive.
        args.extend(objectFiles)

        for libdir in project.libDirs:
            args.append(f"-L{self.ResolveProjectPath(project, libdir)}")
        for lib in project.links:
            if self._IsDirectLibPath(lib):
                args.append(self.ResolveProjectPath(project, lib))
            else:
                args.append(f"-l{lib}")
        args.extend(self.toolchain.ldflags)

        # Sur Windows, les fichiers .bat nécessitent shell=True
        use_shell = linker and (str(linker).endswith('.bat') or str(linker).endswith('.cmd'))
        result = Process.ExecuteCommand(args, captureOutput=True, silent=False, shell=use_shell)
        self._lastResult = result
        return result.returnCode == 0

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        p = Path(lib)
        return p.suffix in (".a", ".bc", ".o", ".so", ".dylib", ".lib") or "/" in lib or "\\" in lib or p.is_absolute()

    def _ResolveOptionBool(self, *names: str):
        """
        Resolve a boolean custom option from builder option tokens.
        Supports:
          - token          -> true  (e.g. emscripten-fullscreen-shell)
          - token=true     -> true
          - token=false    -> false
        Returns:
          True / False / None (not provided)
        """
        tokens = [str(opt).strip().lower() for opt in getattr(self, "options", []) if str(opt).strip()]
        for raw_name in names:
            name = str(raw_name).strip().lower()
            if not name:
                continue
            for token in tokens:
                if token == name:
                    return True
                prefix = f"{name}="
                if token.startswith(prefix):
                    value = token[len(prefix):].strip().lower()
                    if value in ("", "1", "true", "yes", "on"):
                        return True
                    if value in ("0", "false", "no", "off"):
                        return False
                    return True
        return None

    def _ResolveShellFile(self, project: Project) -> str:
        """
        Resolve the Emscripten shell file with this precedence:
          1) project.emscriptenShellFile (explicit)
          2) CLI custom option
             --emscripten-fullscreen-shell / --no-emscripten-fullscreen-shell
          3) project.emscriptenUseFullscreenShell
          4) workspace.emscriptenDefaultFullscreenShell
        """
        explicit = str(getattr(project, 'emscriptenShellFile', '') or '').strip()
        if explicit:
            return explicit

        cli_toggle = self._ResolveOptionBool(
            "emscripten-fullscreen-shell",
            "emscripten-fullscreen",
        )
        if cli_toggle is not None:
            return "emscripten_fullscreen.html" if cli_toggle else ""

        project_toggle = getattr(project, 'emscriptenUseFullscreenShell', None)
        if project_toggle is not None:
            return "emscripten_fullscreen.html" if bool(project_toggle) else ""

        workspace_toggle = bool(getattr(self.workspace, 'emscriptenDefaultFullscreenShell', True))
        return "emscripten_fullscreen.html" if workspace_toggle else ""

    def _GetCompilerFlags(self, project: Project) -> List[str]:
        flags = []

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{self.ResolveProjectPath(project, inc)}")
        pch_file = getattr(project, "_jengaPchFile", "")
        if pch_file:
            flags.extend(["-include-pch", pch_file])

        # Définitions
        for define in self.toolchain.defines:
            flags.append(f"-D{define}")
        for define in project.defines:
            flags.append(f"-D{define}")
        flags.append("-D__EMSCRIPTEN__")

        # Debug
        if project.symbols:
            flags.append("-g")
            flags.append("-gsource-map")  # pour debug

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
        elif warn == "Error":
            flags.append("-Werror")

        # Standard
        if project.language.value == "C++":
            flags.append(f"-std={project.cppdialect.lower()}")
            flags.extend(self.toolchain.cxxflags)
        else:
            flags.append(f"-std={project.cdialect.lower()}")
            flags.extend(self.toolchain.cflags)

        # Flags d'importation des modules C++20 précompilés
        flags.extend(self._GetModuleImportFlags(project))

        return flags

    def _GetLinkerFlags(self, project: Project) -> List[str]:
        flags = []

        # Mode de sortie
        flags.extend(["-s", "WASM=1"])
        flags.extend(["-s", "ALLOW_MEMORY_GROWTH=1"])

        # Custom HTML template (shell file) / fullscreen shell option
        shell_file = self._ResolveShellFile(project)
        if shell_file:
            shell_path = Path(self.ResolveProjectPath(project, shell_file))
            if shell_path.exists():
                flags.extend(["--shell-file", str(shell_path)])
            else:
                # Try template directory
                template_path = Path(__file__).parent.parent.parent / "Templates" / shell_file
                if template_path.exists():
                    flags.extend(["--shell-file", str(template_path)])

        # Canvas ID
        canvas_id = getattr(project, 'emscriptenCanvasId', 'canvas')
        if canvas_id != 'canvas':
            flags.extend(["-s", f"CANVAS_ID='{canvas_id}'"])

        # Initial memory
        initial_memory = getattr(project, 'emscriptenInitialMemory', 16)
        if initial_memory > 0:
            flags.extend(["-s", f"INITIAL_MEMORY={initial_memory}MB"])

        # Stack size
        stack_size = getattr(project, 'emscriptenStackSize', 5)
        if stack_size > 0:
            flags.extend(["-s", f"STACK_SIZE={stack_size}MB"])

        # Export name
        export_name = getattr(project, 'emscriptenExportName', 'Module')
        if export_name != 'Module':
            flags.extend(["-s", f"EXPORT_NAME='{export_name}'"])

        # Extra flags
        extra_flags = getattr(project, 'emscriptenExtraFlags', [])
        if extra_flags:
            flags.extend(extra_flags)

        # Optimisation de la taille
        if self._EnumValue(project.optimize) == "Size":
            flags.append("-Oz")
        for f in project.ldflags:
            if isinstance(f, str):
                flags.extend(shlex.split(f))
            else:
                flags.append(str(f))

        return flags
    
