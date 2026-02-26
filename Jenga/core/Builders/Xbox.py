#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xbox Builder – Compilation Xbox One / Xbox Series X|S.

Modes supportés:
  - gdk (par défaut) : pipeline GDK/GameCore.
  - uwp             : pipeline UWP Dev Mode explicite (sans packaging GDK).
"""

import os
import sys
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

from Jenga.Core.Api import Project, ProjectKind, TargetArch, TargetEnv, TargetOS, CompilerFamily, Toolchain
from ...Utils import Process, FileSystem, Reporter, ProcessResult
from ..Builder import Builder
from ..Toolchains import ToolchainManager
from ..Platform import Platform


class XboxBuilder(Builder):
    """Builder Xbox avec mode GDK (GameCore) et mode UWP (Dev Mode)."""

    _XBOX_PLATFORMS = {
        "XboxOne": "Gaming.Xbox.XboxOne.x64",
        "Scarlett": "Gaming.Xbox.Scarlett.x64",  # Xbox Series X|S
        "Desktop": "Gaming.Desktop.x64",          # GDK Desktop (PC)
        "UWP": "Gaming.UWP.x64",                  # UWP Dev Mode
    }

    _XBOX_PLATFORM_ALIASES = {
        "xboxone": "Gaming.Xbox.XboxOne.x64",
        "xbone": "Gaming.Xbox.XboxOne.x64",
        "xboxseries": "Gaming.Xbox.Scarlett.x64",
        "scarlett": "Gaming.Xbox.Scarlett.x64",
        "xbox": "Gaming.Xbox.Scarlett.x64",
        "desktop": "Gaming.Desktop.x64",
        "pc": "Gaming.Desktop.x64",
        "uwp": "Gaming.UWP.x64",
        "xboxuwp": "Gaming.UWP.x64",
        "gamingxboxxboxonex64": "Gaming.Xbox.XboxOne.x64",
        "gamingxboxscarlettx64": "Gaming.Xbox.Scarlett.x64",
        "gamingdesktopx64": "Gaming.Desktop.x64",
        "gaminguwpx64": "Gaming.UWP.x64",
    }

    _XVC_EXTENSION = ".xvc"
    _MSIXVC_EXTENSION = ".msixvc"

    def _ResolveToolchain(self) -> None:
        """
        Xbox targets are built with MSVC-style tooling, even when target OS is Xbox.
        This override avoids relying on generic target matching against TargetOS.WINDOWS only.
        """
        tc_manager = ToolchainManager(self.workspace)

        msvc_tc = tc_manager.DetectMSVC()
        if msvc_tc:
            self.toolchain = msvc_tc
            return

        # Fallback when VS environment is already initialized in PATH (cl/link/lib available)
        cl_path = Process.Which("cl.exe") or Process.Which("cl")
        link_path = Process.Which("link.exe") or Process.Which("link")
        lib_path = Process.Which("lib.exe") or Process.Which("lib")
        if cl_path and link_path and lib_path:
            tc = Toolchain(
                name="msvc-path",
                compilerFamily=CompilerFamily.MSVC,
                ccPath=cl_path,
                cxxPath=cl_path,
                ldPath=link_path,
                arPath=lib_path,
            )
            tc.targetOs = TargetOS.WINDOWS
            tc.targetArch = self.targetArch
            tc.targetEnv = TargetEnv.MSVC
            self.toolchain = tc
            return

        # Last-resort generic resolver
        super()._ResolveToolchain()

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False,
                 action="build", options=None):
        # Appeler le constructeur parent AVANT toute initialisation spécifique
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose,
                         action=action, options=options)

        if Platform.GetHostOS() != TargetOS.WINDOWS:
            raise RuntimeError("Xbox builds require Windows.")

        self.xbox_mode = self._ResolveXboxMode()
        self.xbox_platform = self._ResolveXboxPlatform()

        self.is_uwp = self.xbox_mode == "uwp"
        self.is_console = (not self.is_uwp) and self.xbox_platform in (
            self._XBOX_PLATFORMS["XboxOne"],
            self._XBOX_PLATFORMS["Scarlett"],
        )
        self.is_desktop = (not self.is_uwp) and self.xbox_platform == self._XBOX_PLATFORMS["Desktop"]

        self.gdk_root: Optional[Path] = None
        self.gdk_edition: Optional[str] = None
        self.gdk_latest: Optional[Path] = None
        self.has_xbox_extensions = False

        if not self.is_uwp:
            self.gdk_root = self._ResolveGDKRoot()
            self.gdk_edition = self._GetGDKEdition()
            self.gdk_latest = self.gdk_root / self.gdk_edition if (self.gdk_root and self.gdk_edition) else None
            self.has_xbox_extensions = self._CheckXboxExtensions()
            if self.is_console and not self.has_xbox_extensions:
                Reporter.Warning(
                    "Xbox Extensions (GDKX) not found. Console packaging requires licensed GDKX. "
                    "Build continues in desktop-compatible mode."
                )

        self._SetupBuildEnvironment()
        # Ne pas appeler _ResolveMSVCToolchain ici car la toolchain a déjà été résolue par _ResolveToolchain
        # On s'assure simplement que les chemins MSVC sont bien définis
        self._EnsureMSVCPaths()

    @staticmethod
    def _NormalizeKey(value: str) -> str:
        return str(value or "").strip().lower().replace(" ", "").replace("-", "").replace("_", "")

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        p = Path(str(lib))
        return p.is_absolute() or p.suffix.lower() in (".lib", ".dll", ".a", ".so", ".dylib") or "/" in str(lib) or "\\" in str(lib)

    def _ResolveXboxMode(self) -> str:
        mode = str(
            getattr(self.workspace, "xboxMode", "")
            or getattr(self.workspace, "xbox_mode", "")
            or ""
        ).strip().lower()

        for token in (self.options or []):
            opt = str(token or "").strip().lower()
            if not opt:
                continue
            if opt in ("uwp", "xbox-uwp", "xbox-mode:uwp", "xbox_mode:uwp"):
                mode = "uwp"
                continue
            if opt in ("gdk", "xbox-gdk", "xbox-mode:gdk", "xbox_mode:gdk"):
                mode = "gdk"
                continue
            if "=" in opt:
                key, value = opt.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key in ("xbox-mode", "xbox_mode"):
                    if value in ("gdk", "uwp"):
                        mode = value

        if mode not in ("gdk", "uwp"):
            mode = "gdk"
        return mode

    def _ResolveXboxPlatform(self) -> str:
        explicit = str(
            getattr(self.workspace, "xboxPlatform", "")
            or getattr(self.workspace, "xbox_platform", "")
            or ""
        ).strip()

        if explicit:
            key = self._NormalizeKey(explicit)
            if key in self._XBOX_PLATFORM_ALIASES:
                return self._XBOX_PLATFORM_ALIASES[key]
            return explicit

        if self.xbox_mode == "uwp":
            return self._XBOX_PLATFORMS["UWP"]

        if self.targetOs == TargetOS.XBOX_ONE:
            return self._XBOX_PLATFORMS["XboxOne"]
        return self._XBOX_PLATFORMS["Scarlett"]

    def _ResolveGDKRoot(self) -> Optional[Path]:
        if self.xbox_mode == "uwp":
            return None

        if "GameDK" in os.environ:
            return Path(os.environ["GameDK"])

        gdk_cfg = getattr(self.workspace, "gdkPath", "") or getattr(self.workspace, "gdk_path", "")
        if gdk_cfg:
            return Path(gdk_cfg)

        if sys.platform == "win32":
            candidates = [
                Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Microsoft GDK",
                Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Microsoft GDK",
                Path("C:\\Microsoft GDK"),
            ]
            for cand in candidates:
                if cand.exists():
                    return cand

        Reporter.Warning("Microsoft GDK not found. Install with: winget install Microsoft.Gaming.GDK")
        return None

    def _GetGDKEdition(self) -> Optional[str]:
        if "GXDKEDITION" in os.environ:
            return os.environ["GXDKEDITION"]
        if "GRDKEDITION" in os.environ:
            return os.environ["GRDKEDITION"]

        if self.gdk_root:
            editions = [d for d in self.gdk_root.iterdir() if d.is_dir() and d.name.isdigit()]
            if editions:
                return sorted(editions, key=lambda p: p.name, reverse=True)[0].name
        return None

    def _CheckXboxExtensions(self) -> bool:
        if not self.gdk_latest:
            return False

        indicators = [
            self.gdk_latest / "GXDK" / "gamekit" / "include" / "Scarlett",
            self.gdk_latest / "GXDK" / "gamekit" / "lib" / "amd64" / "Scarlett",
            self.gdk_latest / "Command Prompts" / "GamingXboxVars.cmd",
        ]
        return any(ind.exists() for ind in indicators)

    def _SetupBuildEnvironment(self) -> None:
        if self.xbox_mode == "uwp":
            os.environ.setdefault("JENGA_XBOX_MODE", "uwp")
            return

        if not self.gdk_root or not self.gdk_edition:
            return

        os.environ.setdefault("GameDK", str(self.gdk_root))
        if self.gdk_latest:
            os.environ.setdefault("GameDKLatest", str(self.gdk_latest))

        if self.is_console:
            os.environ.setdefault("GXDKEDITION", self.gdk_edition)
            if self.gdk_latest:
                os.environ.setdefault("GamingGXDKBuild", str(self.gdk_latest / "GXDK"))
                os.environ.setdefault("GamingGRDKBuild", str(self.gdk_latest / "GRDK"))
        else:
            os.environ.setdefault("GRDKEDITION", self.gdk_edition)
            if self.gdk_latest:
                os.environ.setdefault("GamingGRDKBuild", str(self.gdk_latest / "GRDK"))

    def _EnsureMSVCPaths(self) -> None:
        """Garantit que les chemins des outils MSVC sont résolus, sans écraser la toolchain déjà trouvée."""
        if self.toolchain is None:
            return
        # Si les chemins sont déjà définis, on les garde
        if self.toolchain.ccPath and self.toolchain.ldPath and self.toolchain.arPath:
            return

        resolved_cl = self.toolchain.ccPath or Process.Which("cl.exe") or Process.Which("cl") or "cl.exe"
        self.toolchain.ccPath = resolved_cl
        self.toolchain.cxxPath = self.toolchain.cxxPath or resolved_cl

        link_candidate = None
        lib_candidate = None
        if resolved_cl and resolved_cl != "cl.exe":
            cl_dir = Path(resolved_cl).parent
            cand = cl_dir / "link.exe"
            if cand.exists():
                link_candidate = str(cand)
            cand = cl_dir / "lib.exe"
            if cand.exists():
                lib_candidate = str(cand)

        self.toolchain.ldPath = (
            self.toolchain.ldPath
            or link_candidate
            or Process.Which("link.exe")
            or Process.Which("link")
            or "link.exe"
        )
        self.toolchain.arPath = (
            self.toolchain.arPath
            or lib_candidate
            or Process.Which("lib.exe")
            or Process.Which("lib")
            or "lib.exe"
        )

    def _MapCppDialect(self, dialect: str) -> str:
        value = str(dialect or "").strip().lower()
        if not value:
            return "/std:c++17"
        value = value.replace("gnu++", "c++")
        if value in ("c++latest", "latest", "c++2b", "c++23"):
            return "/std:c++latest"
        if value in ("c++20", "cxx20"):
            return "/std:c++20"
        if value in ("c++17", "cxx17"):
            return "/std:c++17"
        if value in ("c++14", "cxx14"):
            return "/std:c++14"
        return f"/std:{value}" if value.startswith("c++") else "/std:c++17"

    def _GetXboxCompilerFlags(self) -> List[str]:
        flags = [
            "/D_WIN32_WINNT=0x0A00",
            "/DWIN32_LEAN_AND_MEAN",
            "/EHsc",
        ]

        if self.xbox_mode == "uwp":
            flags.extend([
                "/DWINAPI_FAMILY=WINAPI_FAMILY_APP",
                "/DWINAPI_FAMILY_PARTITION=WINAPI_PARTITION_APP",
                "/D__XBOX_UWP_DEV_MODE__",
            ])
        else:
            flags.extend([
                "/DWINAPI_FAMILY=WINAPI_FAMILY_GAMES" if self.is_console else "/DWINAPI_FAMILY=WINAPI_FAMILY_DESKTOP_APP",
                "/D__XBOXCORE__" if self.is_console else "",
                "/D__XBOX_DESKTOP__" if self.is_desktop else "",
            ])

        if self.targetArch == TargetArch.X86_64:
            flags.append("/arch:AVX2")

        if self.gdk_latest and self.xbox_mode == "gdk":
            if self.is_console and self.has_xbox_extensions:
                scarlett_inc = self.gdk_latest / "GXDK" / "gamekit" / "include" / "Scarlett"
                if scarlett_inc.exists():
                    flags.append(f"/I{scarlett_inc}")
            gdk_inc = self.gdk_latest / "GRDK" / "gamekit" / "include"
            if gdk_inc.exists():
                flags.append(f"/I{gdk_inc}")

        return [f for f in flags if f]

    def _GetXboxLinkerFlags(self) -> List[str]:
        flags: List[str] = []

        if self.xbox_mode == "uwp":
            flags.append("windowsapp.lib")
            return flags

        if self.is_console:
            flags.extend(["XGamePlatform.lib", "XGameRuntime.lib", "xg_scratch.lib", "xmem.lib"])
        else:
            flags.append("XGameRuntime.lib")

        if self.gdk_latest:
            if self.is_console and self.has_xbox_extensions:
                scarlett_lib = self.gdk_latest / "GXDK" / "gamekit" / "lib" / "amd64" / "Scarlett"
                if scarlett_lib.exists():
                    flags.append(f"/LIBPATH:{scarlett_lib}")
                gxdk_lib = self.gdk_latest / "GXDK" / "gamekit" / "lib" / "amd64"
                if gxdk_lib.exists():
                    flags.append(f"/LIBPATH:{gxdk_lib}")

            grdk_lib = self.gdk_latest / "GRDK" / "gamekit" / "lib" / "amd64"
            if grdk_lib.exists():
                flags.append(f"/LIBPATH:{grdk_lib}")

        return flags

    def GetObjectExtension(self) -> str:
        return ".obj"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dll"
        if project.kind == ProjectKind.STATIC_LIB:
            return ".lib"
        return ".exe"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> ProcessResult:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [
            compiler,
            "/c",
            f"/Fo{obj}",
            "/nologo",
            f"/I{self.ResolveProjectPath(project, '.')}",
        ]

        for inc in project.includeDirs:
            args.append(f"/I{self.ResolveProjectPath(project, inc)}")

        for define in getattr(self.toolchain, "defines", []):
            args.append(f"/D{define}")
        for define in project.defines:
            args.append(f"/D{define}")

        if self.config.lower() == "debug" or project.symbols:
            args.extend(["/Od", "/Zi", "/MDd"])
        else:
            opt = project.optimize.value if hasattr(project.optimize, "value") else project.optimize
            if opt in ("Speed", "Full"):
                args.append("/O2")
            elif opt == "Size":
                args.append("/O1")
            else:
                args.append("/Od")
            args.append("/MD")

        warn = project.warnings.value if hasattr(project.warnings, "value") else project.warnings
        if warn == "All":
            args.append("/W4")
        elif warn == "Extra":
            args.append("/W3")
        elif warn == "Error":
            args.append("/WX")

        if project.language.value in ("C++", "Objective-C++"):
            args.append(self._MapCppDialect(project.cppdialect))
            args.extend(getattr(self.toolchain, "cxxflags", []))
            args.extend(project.cxxflags)
        else:
            if project.cdialect:
                cstd = str(project.cdialect).strip().lower().replace("gnu", "c")
                if cstd:
                    args.append(f"/std:{cstd}")
            args.extend(getattr(self.toolchain, "cflags", []))
            args.extend(project.cflags)

        args.extend(self._GetXboxCompilerFlags())
        args.extend(self.GetModuleFlags(project, sourceFile))
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        if not self.IsModuleFile(sourceFile):
            return []
        ifc_name = Path(sourceFile).with_suffix(".ifc").name
        ifc_path = self.GetObjectDir(project) / ifc_name
        return ["/interface", "/std:c++latest", f"/ifcOutput{ifc_path}"]

    def _ResolveLinkItem(self, project: Project, item: str) -> str:
        raw = str(item or "").strip()
        if not raw:
            return ""
        if self._IsDirectLibPath(raw):
            return self.ResolveProjectPath(project, raw)
        if raw.lower().endswith(".lib"):
            return raw
        return f"{raw}.lib"

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            args = [self.toolchain.arPath or "lib.exe", "/NOLOGO", f"/OUT:{out}"]
            args.extend(objectFiles)
            result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
            self._lastResult = result
            return result.returnCode == 0

        args = [self.toolchain.ldPath or "link.exe", "/NOLOGO", f"/OUT:{out}", "/DYNAMICBASE", "/NXCOMPAT"]

        if project.kind == ProjectKind.SHARED_LIB:
            args.append("/DLL")
        elif project.kind == ProjectKind.WINDOWED_APP:
            args.append("/SUBSYSTEM:WINDOWS")
        else:
            args.append("/SUBSYSTEM:CONSOLE")

        if self.xbox_mode == "uwp":
            args.append("/APPCONTAINER")

        if self.config.lower() == "debug":
            args.append("/DEBUG:FULL")

        args.extend(objectFiles)

        for libdir in project.libDirs:
            args.append(f"/LIBPATH:{self.ResolveProjectPath(project, libdir)}")

        if self.xbox_mode != "uwp":
            args.extend(["kernel32.lib", "user32.lib", "ole32.lib", "oleaut32.lib"])

        for lib in project.links:
            link_item = self._ResolveLinkItem(project, lib)
            if link_item:
                args.append(link_item)

        args.extend(getattr(self.toolchain, "ldflags", []))
        args.extend(project.ldflags)
        args.extend(self._GetXboxLinkerFlags())

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def BuildProject(self, project: Project) -> bool:
        Reporter.Info(f"Building Xbox project {project.name} (mode={self.xbox_mode}, platform={self.xbox_platform})")

        if not super().BuildProject(project):
            return False

        # UWP Dev Mode: no GDK packaging pipeline.
        if self.is_uwp:
            Reporter.Detail("UWP mode active: skipping MicrosoftGame.config/layout/XVC packaging.")
            return True

        # Libraries are valid outputs for Xbox toolchain; packaging applies to apps only.
        if project.kind in (ProjectKind.STATIC_LIB, ProjectKind.SHARED_LIB):
            Reporter.Detail("Library target: skipping Xbox packaging pipeline.")
            return True

        config_file = self._GenerateMicrosoftGameConfig(project)
        if not config_file:
            return False

        layout_dir = self._CreateLooseLayout(project)
        if not layout_dir:
            return False

        # Copier les assets supplémentaires (chunks)
        self._CopyAssets(project, layout_dir)

        if self.is_console and self.has_xbox_extensions:
            xvc_package = self._CreateXVCPackage(project, layout_dir)
            if not xvc_package:
                Reporter.Warning("XVC package creation failed, keeping loose layout only.")

        if getattr(project, "xboxSigningMode", "test"):
            self._SignPackage(project, layout_dir)

        return True

    def _GenerateMicrosoftGameConfig(self, project: Project) -> Optional[Path]:
        output_dir = Path(self.GetTargetDir(project)) / "xbox-config"
        FileSystem.MakeDirectory(output_dir)
        config_path = output_dir / "MicrosoftGame.config"

        package_name = getattr(project, "xboxPackageName", "") or f"{project.name}.Game"
        publisher = getattr(project, "xboxPublisher", "") or "Jenga"
        version = getattr(project, "xboxVersion", "") or "1.0.0.0"

        root = ET.Element("Game", {
            "xmlns": "http://schemas.microsoft.com/xbox/microsoftgame/2018",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        })

        identity = ET.SubElement(root, "Identity")
        ET.SubElement(identity, "Name").text = package_name
        ET.SubElement(identity, "Publisher").text = publisher
        ET.SubElement(identity, "Version").text = version

        properties = ET.SubElement(root, "Properties")
        ET.SubElement(properties, "DisplayName").text = project.targetName or project.name
        ET.SubElement(properties, "Description").text = getattr(project, "description", f"{project.name} built with Jenga")
        ET.SubElement(properties, "ExecutableName").text = f"{project.targetName or project.name}.exe"
        ET.SubElement(properties, "ExecutablePath").text = f"{project.targetName or project.name}.exe"

        ET.ElementTree(root).write(config_path, encoding="utf-8", xml_declaration=True)
        Reporter.Detail(f"Generated MicrosoftGame.config: {config_path}")
        return config_path

    def _CreateLooseLayout(self, project: Project) -> Optional[Path]:
        target_exe = self.GetTargetPath(project)
        if not target_exe.exists():
            Reporter.Error(f"Executable not found: {target_exe}")
            return None

        layout_dir = Path(self.GetTargetDir(project)) / self.xbox_platform
        FileSystem.RemoveDirectory(layout_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(layout_dir)

        exe_name = f"{project.targetName or project.name}.exe"
        shutil.copy2(target_exe, layout_dir / exe_name)

        # Copier les DLLs provenant des dépendances
        for dep_name in project.dependsOn:
            dep_proj = self.workspace.projects.get(dep_name)
            if not dep_proj:
                continue
            if dep_proj.kind == ProjectKind.SHARED_LIB:
                dep_out = self.GetTargetPath(dep_proj)
                if dep_out.exists() and dep_out.suffix.lower() == ".dll":
                    shutil.copy2(dep_out, layout_dir / dep_out.name)

        # Copier les fichiers de dependFiles (générique)
        for dep in project.dependFiles:
            dep_path = Path(self.ResolveProjectPath(project, dep))
            if dep_path.suffix.lower() == ".dll" and dep_path.exists():
                shutil.copy2(dep_path, layout_dir / dep_path.name)

        config_src = layout_dir.parent / "xbox-config" / "MicrosoftGame.config"
        if config_src.exists():
            shutil.copy2(config_src, layout_dir / "MicrosoftGame.config")

        Reporter.Success(f"Loose layout created: {layout_dir}")
        return layout_dir

    def _CopyAssets(self, project: Project, layout_dir: Path) -> None:
        """Copie les assets définis dans xboxAssetChunks dans le layout."""
        asset_patterns = getattr(project, "xboxAssetChunks", [])
        if not asset_patterns:
            return

        for pattern in asset_patterns:
            resolved_pattern = self.ResolveProjectPath(project, pattern)
            # Utiliser glob pour trouver les fichiers correspondants
            import glob
            for src_path in glob.glob(resolved_pattern, recursive=True):
                src = Path(src_path)
                if not src.is_file():
                    continue
                # Calculer le chemin relatif par rapport au pattern ?
                # Pour simplifier, on copie dans un sous-dossier "Assets" en conservant l'arborescence
                # On enlève la partie commune du pattern pour déterminer le chemin relatif
                # Exemple simple : on prend le nom du fichier
                dest = layout_dir / "Assets" / src.name
                FileSystem.MakeDirectory(dest.parent)
                shutil.copy2(src, dest)

    def _CreateXVCPackage(self, project: Project, layout_dir: Path) -> Optional[Path]:
        if not self.gdk_latest:
            Reporter.Error("GDK not found, cannot create XVC package")
            return None

        makepkg_path = self.gdk_latest / "bin" / "MakePkg.exe"
        if not makepkg_path.exists():
            Reporter.Error(f"MakePkg.exe not found at {makepkg_path}")
            return None

        package_dir = Path(self.GetTargetDir(project)) / "packages"
        FileSystem.MakeDirectory(package_dir)

        mapping_file = self._GenerateMappingFile(project, layout_dir, package_dir)
        if not mapping_file:
            return None

        signing_mode = getattr(project, "xboxSigningMode", "test")
        package_name = getattr(project, "xboxPackageName", "") or project.name
        package_version = getattr(project, "xboxVersion", "") or "1.0.0.0"
        publisher_id = "8wekyb3d8bbwe"

        xvc_filename = f"{package_name}_{package_version}_neutral__{publisher_id}{self._XVC_EXTENSION}"
        xvc_path = package_dir / xvc_filename

        cmd = [
            str(makepkg_path), "pack",
            "/f", str(mapping_file),
            "/d", str(layout_dir),
            "/pd", str(package_dir),
        ]

        if signing_mode == "test":
            cmd.append("/lt")
        elif signing_mode == "random":
            cmd.append("/l")
        elif signing_mode == "stable":
            lekb_path = getattr(project, "xboxLEKBPath", None)
            if lekb_path:
                cmd.extend(["/lk", str(lekb_path)])
            else:
                Reporter.Warning("Stable signing requested without LEKB, fallback to test signing")
                cmd.append("/lt")

        if self.xbox_platform == self._XBOX_PLATFORMS["Scarlett"]:
            cmd.append("/xs")
        else:
            cmd.append("/x")

        if self.is_console:
            gameos_path = self.gdk_latest / "GXDK" / "gamekit" / "data" / "GameOS.xvd"
            if gameos_path.exists():
                cmd.extend(["/gameos", str(gameos_path.parent)])

        Reporter.Info(f"Creating XVC package: {xvc_filename}")
        result = Process.ExecuteCommand(cmd, captureOutput=True, silent=False)
        self._lastResult = result
        if result.returnCode == 0:
            self._RunSubmissionValidator(package_dir, xvc_path)
            Reporter.Success(f"XVC package created: {xvc_path}")
            return xvc_path

        Reporter.Error(f"MakePkg failed with code {result.returnCode}")
        return None

    def _GenerateMappingFile(self, project: Project, layout_dir: Path, output_dir: Path) -> Optional[Path]:
        mapping_path = output_dir / "chunks.xml"

        root = ET.Element("Mapping", {"xmlns": "http://schemas.microsoft.com/xbox/mapping/2017"})
        # Chunk 0: exécutable et config
        chunk0 = ET.SubElement(root, "Chunk", {"id": "0"})
        ET.SubElement(chunk0, "FileGroup", {"path": "*.exe"})
        ET.SubElement(chunk0, "FileGroup", {"path": "MicrosoftGame.config"})

        # Chunk 1: DLLs
        chunk1 = ET.SubElement(root, "Chunk", {"id": "1"})
        ET.SubElement(chunk1, "FileGroup", {"path": "*.dll"})

        # Chunks supplémentaires pour les assets (relatifs au layout)
        asset_chunks = list(getattr(project, "xboxAssetChunks", []) or [])
        for i, asset_pattern in enumerate(asset_chunks, start=2):
            # On suppose que les assets sont copiés dans le layout, donc le chemin est relatif
            # Mais comme ils peuvent être dans des sous-dossiers, on utilise le pattern tel quel
            # MakePkg comprend les globs
            chunk = ET.SubElement(root, "Chunk", {"id": str(i)})
            ET.SubElement(chunk, "FileGroup", {"path": asset_pattern})

        ET.ElementTree(root).write(mapping_path, encoding="utf-8", xml_declaration=True)
        Reporter.Detail(f"Generated mapping file: {mapping_path}")
        return mapping_path

    def _RunSubmissionValidator(self, package_dir: Path, package_path: Path) -> None:
        if not self.gdk_latest:
            return

        validator_path = self.gdk_latest / "bin" / "SubmissionValidator.dll"
        if not validator_path.exists():
            Reporter.Warning("SubmissionValidator.dll not found, skipping validation")
            return

        # Vérifier que dotnet est disponible
        dotnet_path = Process.Which("dotnet")
        if not dotnet_path:
            Reporter.Warning("dotnet not found in PATH, skipping submission validation")
            return

        log_path = package_dir / "submission_validation.xml"
        cmd = ["dotnet", str(validator_path), "validate", "-p", str(package_path), "-o", str(log_path)]
        result = Process.ExecuteCommand(cmd, captureOutput=True, silent=False)
        self._lastResult = result

        if result.returnCode == 0:
            Reporter.Success("Submission validation passed")
        else:
            Reporter.Error(f"Submission validation failed. Check log: {log_path}")

    def _SignPackage(self, project: Project, layout_dir: Path) -> None:
        signing_mode = getattr(project, "xboxSigningMode", "test")
        if signing_mode == "stable":
            lekb_path = getattr(project, "xboxLEKBPath", None)
            if not lekb_path:
                lekb_path = self._GenerateLEKB(project)
                if lekb_path:
                    project.xboxLEKBPath = str(lekb_path)

    def _GenerateLEKB(self, project: Project) -> Optional[Path]:
        if not self.gdk_latest:
            return None

        makepkg_path = self.gdk_latest / "bin" / "MakePkg.exe"
        if not makepkg_path.exists():
            return None

        workspace_root = Path(self.workspace.location or ".").resolve()
        key_dir = workspace_root / ".jenga" / "keys"
        FileSystem.MakeDirectory(key_dir)

        lekb_path = key_dir / f"{project.name}_secret.lekb"
        cmd = [str(makepkg_path), "genkey", "/ekb", str(lekb_path)]
        result = Process.ExecuteCommand(cmd, captureOutput=True, silent=False)
        self._lastResult = result

        if result.returnCode == 0:
            Reporter.Warning(f"LEKB generated at {lekb_path}. Keep this file secret.")
            return lekb_path

        Reporter.Error("Failed to generate LEKB")
        return None

    def DeployToConsole(self, project: Project, layout_dir: Path, console_ip: Optional[str] = None) -> bool:
        if not self.gdk_latest:
            Reporter.Error("GDK not found, cannot deploy")
            return False

        xbapp_path = self.gdk_latest / "bin" / "xbapp.exe"
        if not xbapp_path.exists():
            Reporter.Error(f"xbapp.exe not found at {xbapp_path}")
            return False

        cmd = [str(xbapp_path), "deploy", str(layout_dir)]
        if console_ip:
            cmd.extend(["/s", console_ip])

        result = Process.ExecuteCommand(cmd, captureOutput=True, silent=False)
        self._lastResult = result
        if result.returnCode == 0:
            Reporter.Success("Deployed to console")
            return True

        Reporter.Error("Deployment failed")
        return False

    def LaunchOnConsole(self, project: Project, console_ip: Optional[str] = None) -> bool:
        if not self.gdk_latest:
            return False

        xbapp_path = self.gdk_latest / "bin" / "xbapp.exe"
        exe_name = f"{project.targetName or project.name}.exe"

        cmd = [str(xbapp_path), "launch", exe_name]
        if console_ip:
            cmd.extend(["/s", console_ip])

        result = Process.ExecuteCommand(cmd, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0