#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
macOS Builder – Compilation pour macOS (Mach-O).
Supporte Apple Clang.
Gère les .dylib, .a, .app bundles, frameworks.
"""

from pathlib import Path
from typing import List, Optional
import plistlib
import shutil

from Jenga.Core.Api import Project, ProjectKind, CompilerFamily, TargetArch
from ...Utils import Process, FileSystem, ProcessResult, Colored
from ..Builder import Builder
from ..IconConverter import (
    ResolveIconFor, DetectIconFormat, ConvertPngToIcns, HasPillow,
    PLATFORM_MACOS, FORMAT_PNG, FORMAT_JPG, FORMAT_ICNS,
)


class MacOSBuilder(Builder):
    """
    Builder pour macOS.
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)
        # Apple Clang ou Clang standard
        self.is_apple_clang = self.toolchain.compilerFamily == CompilerFamily.APPLE_CLANG
        self._objcxxProbeCache = {}

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        """Return True if lib is a direct path (contains slash or extension)."""
        p = Path(lib)
        return p.suffix in (".a", ".dylib", ".so", ".framework", ".lib") or "/" in lib or "\\" in lib or p.is_absolute()

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

    def _NeedsObjectiveCppMode(self, sourcePath: Path) -> bool:
        """Detect C++ sources that must be compiled as Objective-C++ on macOS."""
        ext = sourcePath.suffix.lower()
        if ext == ".mm":
            return True
        if ext not in (".cpp", ".cc", ".cxx", ".c++", ".cp"):
            return False

        key = str(sourcePath.resolve())
        if key in self._objcxxProbeCache:
            return self._objcxxProbeCache[key]

        needs_objcpp = False
        try:
            content = sourcePath.read_text(encoding="utf-8", errors="ignore")
            # NkMain.h includes Cocoa/UIKit entry-points with Objective-C syntax.
            needs_objcpp = "NkMain.h" in content or "#import <Cocoa/Cocoa.h>" in content
        except Exception:
            needs_objcpp = False

        self._objcxxProbeCache[key] = needs_objcpp
        return needs_objcpp

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> ProcessResult:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [compiler]
        if self._NeedsObjectiveCppMode(src):
            args.extend(["-x", "objective-c++"])
        args.extend(["-c", "-o", str(obj)])
        args.extend(self.GetDependencyFlags(str(obj)))
        args.extend(self._GetCompilerFlags(project))
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        if not self.IsModuleFile(sourceFile):
            return []
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
            # Put objects first so following libraries/frameworks can satisfy symbols.
            args.extend(objectFiles)

            # Framework paths
            for fw_path in getattr(self.toolchain, 'frameworkPaths', []):
                args.append(f"-F{fw_path}")
            # Frameworks (toolchain)
            for fw in getattr(self.toolchain, 'frameworks', []):
                args.extend(["-framework", fw])
            # Frameworks (project)
            for fw in project.frameworks:
                args.extend(["-framework", fw])
            # Default Apple frameworks for macOS app/test targets.
            # This ensures Objective-C runtime symbols and common platform APIs
            # used by Cocoa backends are resolved even when workspaces omit explicit frameworks.
            if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
                default_frameworks = [
                    "Cocoa",
                    "QuartzCore",
                    "CoreGraphics",
                    "GameController",
                    "AVFoundation",
                    "CoreMedia",
                    "CoreVideo",
                ]
                toolchain_frameworks = set(getattr(self.toolchain, "frameworks", []) or [])
                project_frameworks = set(project.frameworks or [])
                for fw in default_frameworks:
                    if fw in toolchain_frameworks or fw in project_frameworks:
                        continue
                    args.extend(["-framework", fw])
            # Library directories
            for libdir in project.libDirs:
                args.append(f"-L{self.ResolveProjectPath(project, libdir)}")
            # Libraries (links)
            for lib in project.links:
                if self._IsDirectLibPath(lib):
                    args.append(self.ResolveProjectPath(project, lib))
                else:
                    args.append(f"-l{lib}")
            # RPATH
            args.append("-Wl,-rpath,@loader_path")
            # Toolchain ldflags
            args.extend(self.toolchain.ldflags)
            # Project ldflags
            args.extend(project.ldflags)

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        if result.returnCode != 0:
            return False

        # Si c'est une app windowed avec icone configuree, on cree un bundle
        # .app minimal a cote de l'exe pour que l'icone soit visible dans
        # Finder. L'exe standalone reste accessible pour les workflows CLI.
        if project.kind == ProjectKind.WINDOWED_APP:
            self._CreateMacosAppBundle(project, out)

        return True

    # -----------------------------------------------------------------------
    # App bundle .app minimal pour macOS (avec icone)
    # -----------------------------------------------------------------------

    def _CreateMacosAppBundle(self, project: Project, exe_path: Path) -> Optional[Path]:
        """
        Cree (ou met a jour) un bundle .app minimal a cote de l'executable :
          <exe>.app/
            Contents/
              Info.plist        (CFBundleExecutable + CFBundleIconFile)
              MacOS/<exe>       (copie de l'exe)
              Resources/AppIcon.icns

        Ne fait rien si aucune icone macOS n'est configuree.
        Retourne le path du bundle ou None.
        """
        icon_src = ResolveIconFor(project, PLATFORM_MACOS)
        if not icon_src:
            return None

        icon_path = Path(self.ResolveProjectPath(project, icon_src))
        if not icon_path.exists():
            Colored.PrintWarn(
                f"[macOS:icon] icone configuree introuvable : {icon_path}"
            )
            return None

        bundle_name = (project.targetName or project.name) + ".app"
        bundle_dir  = exe_path.parent / bundle_name
        macos_dir   = bundle_dir / "Contents" / "MacOS"
        res_dir     = bundle_dir / "Contents" / "Resources"
        macos_dir.mkdir(parents=True, exist_ok=True)
        res_dir.mkdir  (parents=True, exist_ok=True)

        # 1) Copie de l'executable dans Contents/MacOS/. On garde aussi l'exe
        #    standalone pour les workflows non-bundle (jenga run, CI).
        exe_name = exe_path.name
        try:
            shutil.copy2(exe_path, macos_dir / exe_name)
        except Exception as e:
            Colored.PrintWarn(f"[macOS:icon] copie exe -> bundle echouee : {e}")
            return None

        # 2) Conversion de l'icone en .icns (ou copie si deja .icns).
        icns_path = res_dir / "AppIcon.icns"
        fmt = DetectIconFormat(icon_path)
        if fmt == FORMAT_ICNS:
            try:
                shutil.copy2(icon_path, icns_path)
            except Exception:
                return None
        elif fmt in (FORMAT_PNG, FORMAT_JPG):
            if not HasPillow():
                Colored.PrintWarn(
                    "[macOS:icon] Pillow non installe -- conversion PNG->ICNS "
                    "ignoree. Installer : pip install Pillow"
                )
                return None
            if not ConvertPngToIcns(icon_path, icns_path):
                Colored.PrintWarn(f"[macOS:icon] conversion PNG->ICNS echouee : {icon_path}")
                return None
        else:
            Colored.PrintWarn(
                f"[macOS:icon] format non supporte ({fmt}) pour macOS : {icon_path}"
            )
            return None

        # 3) Info.plist minimal. CFBundleIconFile pointe sur AppIcon (sans .icns).
        plist = {
            "CFBundleExecutable":      exe_name,
            "CFBundleIdentifier":      f"com.jenga.{project.name.lower()}",
            "CFBundleName":            project.name,
            "CFBundlePackageType":     "APPL",
            "CFBundleShortVersionString": "1.0",
            "CFBundleVersion":         "1",
            "CFBundleIconFile":        "AppIcon",
        }
        plist_path = bundle_dir / "Contents" / "Info.plist"
        try:
            with open(plist_path, "wb") as f:
                plistlib.dump(plist, f)
        except Exception as e:
            Colored.PrintWarn(f"[macOS:icon] ecriture Info.plist echouee : {e}")
            return None

        return bundle_dir

    def _GetCompilerFlags(self, project: Project) -> List[str]:
        flags = []

        # Sysroot (if defined in toolchain)
        if self.toolchain.sysroot:
            flags.append(f"-isysroot{self.toolchain.sysroot}")

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{self.ResolveProjectPath(project, inc)}")

        # Defines (toolchain)
        for define in self.toolchain.defines:
            flags.append(f"-D{define}")
        # Defines (project)
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

        # Position Independent Code
        if project.kind == ProjectKind.SHARED_LIB:
            flags.append("-fPIC")

        # Architecture
        if self.targetArch == TargetArch.ARM64:
            flags.extend(["-arch", "arm64"])
        elif self.targetArch == TargetArch.X86_64:
            flags.extend(["-arch", "x86_64"])

        return flags