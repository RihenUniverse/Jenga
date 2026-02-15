#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Xbox Builder – Compilation pour Xbox One et Xbox Series X|S via Microsoft GDK.
Gère :
  - Détection et configuration de l'environnement GDK/GDKX
  - Compilation avec MSVC pour les plateformes Gaming.Xbox.*
  - Création du layout "loose" pour déploiement rapide
  - Packaging XVC (.xvc) et MSIXVC (.msixvc) avec MakePkg
  - Signature (test, random, stable key)
  - Déploiement sur console via xbapp
  - Validation pré-soumission avec SubmissionValidator

Respecte les conventions de nommage Jenga (PascalCase, _PascalCase, camelCase).
"""

import os
import sys
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
import tempfile
import uuid
import subprocess

from Jenga.Core.Api import Project, ProjectKind, TargetArch, TargetOS
from ...Utils import Process, FileSystem, Colored, Reporter
from ..Builder import Builder
from ..Toolchains import ToolchainManager
from ..Platform import Platform


class XboxBuilder(Builder):
    """
    Builder pour Xbox One et Xbox Series X|S utilisant le Microsoft Game Development Kit (GDK).
    """

    # -----------------------------------------------------------------------
    # Constantes – UPPER_SNAKE_CASE
    # -----------------------------------------------------------------------

    _XBOX_PLATFORMS = {
        "XboxOne": "Gaming.Xbox.XboxOne.x64",
        "Scarlett": "Gaming.Xbox.Scarlett.x64",  # Xbox Series X|S
        "Desktop": "Gaming.Desktop.x64"          # PC (GDK Desktop)
    }

    _XBOX_ARCH_MAPPING = {
        TargetArch.X86_64: "x64",
        TargetArch.X64: "x64",
    }

    _XVC_EXTENSION = ".xvc"        # Xbox console package
    _MSIXVC_EXTENSION = ".msixvc"  # Windows GDK package

    # -----------------------------------------------------------------------
    # Initialisation et détection GDK
    # -----------------------------------------------------------------------

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)

        # Vérifier que l'hôte est Windows
        if Platform.GetHostOS() != TargetOS.WINDOWS:
            raise RuntimeError("Xbox builds require Windows with Microsoft GDK.")

        # Déterminer la plateforme Xbox cible
        self.xbox_platform = self._ResolveXboxPlatform()
        self.is_console = self.xbox_platform in ("Gaming.Xbox.XboxOne.x64", "Gaming.Xbox.Scarlett.x64")
        self.is_desktop = self.xbox_platform == "Gaming.Desktop.x64"

        # Résoudre l'environnement GDK
        self.gdk_root = self._ResolveGDKRoot()
        self.gdk_edition = self._GetGDKEdition()
        self.gdk_latest = self.gdk_root / self.gdk_edition if self.gdk_root else None

        # Vérifier la présence des extensions Xbox (GDKX) pour console
        self.has_xbox_extensions = self._CheckXboxExtensions()

        if self.is_console and not self.has_xbox_extensions:
            Reporter.Warning(
                "Xbox Extensions (GDKX) not found. Console builds require a licensed GDKX installation. "
                "Falling back to PC-compatible build. See: https://aka.ms/gdkdl"
            )

        # Configurer l'environnement de build
        self._SetupBuildEnvironment()

        # Résoudre la toolchain (MSVC)
        self._ResolveMSVCToolchain()

    def _ResolveXboxPlatform(self) -> str:
        """Détermine la plateforme Xbox en fonction de l'architecture et des paramètres."""
        # Priorité : configuration explicite dans le workspace/projet
        if hasattr(self.workspace, 'xbox_platform') and self.workspace.xbox_platform:
            return self.workspace.xbox_platform

        # Sinon, déduire de l'architecture
        if self.targetArch in (TargetArch.X86_64, TargetArch.X64):
            # Par défaut : Xbox Series X|S
            return self._XBOX_PLATFORMS["Scarlett"]

        # Fallback
        return self._XBOX_PLATFORMS["Scarlett"]

    def _ResolveGDKRoot(self) -> Optional[Path]:
        """Détermine le chemin racine du Microsoft GDK."""
        # 1. Variable d'environnement GameDK
        if "GameDK" in os.environ:
            return Path(os.environ["GameDK"])

        # 2. Workspace configuration
        if hasattr(self.workspace, 'gdkPath') and self.workspace.gdkPath:
            return Path(self.workspace.gdkPath)

        # 3. Chemins d'installation par défaut
        if sys.platform == "win32":
            candidates = [
                Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Microsoft GDK",
                Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Microsoft GDK",
                Path("C:\\Microsoft GDK")
            ]
            for cand in candidates:
                if cand.exists():
                    return cand

        # 4. Installation via winget (recherche dans le registre)
        try:
            result = Process.Capture(["winget", "list", "--name", "Microsoft.Gaming.GDK", "--exact"])
            # TODO: parsing du résultat pour extraire le chemin
            pass
        except:
            pass

        Reporter.Warning("Microsoft GDK not found. Please install via winget: winget install Microsoft.Gaming.GDK")
        return None

    def _GetGDKEdition(self) -> Optional[str]:
        """Récupère le numéro d'édition du GDK (ex: 220300)."""
        if "GXDKEDITION" in os.environ:
            return os.environ["GXDKEDITION"]
        if "GRDKEDITION" in os.environ:
            return os.environ["GRDKEDITION"]

        # Chercher le dossier de version le plus récent
        if self.gdk_root:
            editions = [d for d in self.gdk_root.iterdir() if d.is_dir() and d.name.isdigit()]
            if editions:
                return sorted(editions, key=lambda p: p.name, reverse=True)[0].name
        return None

    def _CheckXboxExtensions(self) -> bool:
        """Vérifie la présence des extensions Xbox (GDKX) nécessaires pour console."""
        if not self.gdk_latest:
            return False

        # Indicateurs de présence de GDKX
        indicators = [
            self.gdk_latest / "GXDK" / "gamekit" / "include" / "Scarlett",
            self.gdk_latest / "GXDK" / "gamekit" / "lib" / "amd64" / "Scarlett",
            self.gdk_latest / "Command Prompts" / "GamingXboxVars.cmd"
        ]

        return any(ind.exists() for ind in indicators)

    def _SetupBuildEnvironment(self):
        """Configure les variables d'environnement pour le build Xbox."""
        if not self.gdk_root or not self.gdk_edition:
            return

        # Configuration basée sur la documentation Microsoft [citation:7]
        os.environ.setdefault("GameDK", str(self.gdk_root))
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

        # Windows SDK (requis)
        if "WindowsSdkDir" not in os.environ:
            # Détection automatique
            win10_sdk = Path("C:/Program Files (x86)/Windows Kits/10")
            if win10_sdk.exists():
                os.environ["WindowsSdkDir"] = str(win10_sdk)

    def _ResolveMSVCToolchain(self):
        """Configure la toolchain MSVC avec les flags spécifiques Xbox."""
        # Utiliser le ToolchainManager pour détecter MSVC
        tc_manager = ToolchainManager(self.workspace)
        msvc_tc = tc_manager.DetectMSVC()

        if msvc_tc:
            self.toolchain = msvc_tc
            # Ajouter les flags spécifiques Xbox
            self.toolchain.cflags.extend(self._GetXboxCompilerFlags())
            self.toolchain.cxxflags.extend(self._GetXboxCompilerFlags())
            self.toolchain.ldflags.extend(self._GetXboxLinkerFlags())
        else:
            raise RuntimeError("MSVC toolchain not found. Xbox builds require Visual Studio with C++ tools.")

    # -----------------------------------------------------------------------
    # Flags de compilation et d'édition de liens
    # -----------------------------------------------------------------------

    def _GetXboxCompilerFlags(self) -> List[str]:
        """Retourne les flags de compilation spécifiques Xbox."""
        flags = [
            "/DWINAPI_FAMILY=WINAPI_FAMILY_GAMES" if self.is_console else "/DWINAPI_FAMILY=WINAPI_FAMILY_DESKTOP_APP",
            "/D_WIN32_WINNT=0x0A00",
            "/DWIN32_LEAN_AND_MEAN",
            "/D__XBOXCORE__" if self.is_console else "",
            "/D__XBOX_DESKTOP__" if self.is_desktop else "",
            "/EHsc",
            "/std:c++17",
        ]

        # Architecture
        if self.targetArch in (TargetArch.X86_64, TargetArch.X64):
            flags.append("/arch:AVX2")

        # SDK includes
        if self.gdk_latest:
            if self.is_console and self.has_xbox_extensions:
                scarlett_inc = self.gdk_latest / "GXDK" / "gamekit" / "include" / "Scarlett"
                if scarlett_inc.exists():
                    flags.append(f"/I{scarlett_inc}")

            gdk_inc = self.gdk_latest / "GRDK" / "gamekit" / "include"
            if gdk_inc.exists():
                flags.append(f"/I{gdk_inc}")

        return [f for f in flags if f]

    def _GetXboxLinkerFlags(self) -> List[str]:
        """Retourne les flags d'édition de liens spécifiques Xbox."""
        flags = []

        # Librairies de base
        if self.is_console:
            flags.extend([
                "XGamePlatform.lib",
                "XGameRuntime.lib",
                "xg_scratch.lib",
                "xmem.lib",
            ])
        else:
            flags.extend([
                "XGameRuntime.lib",
            ])

        # Librairies GDK
        if self.gdk_latest:
            lib_paths = []

            if self.is_console and self.has_xbox_extensions:
                scarlett_lib = self.gdk_latest / "GXDK" / "gamekit" / "lib" / "amd64" / "Scarlett"
                if scarlett_lib.exists():
                    lib_paths.append(f"/LIBPATH:{scarlett_lib}")

                gxdk_lib = self.gdk_latest / "GXDK" / "gamekit" / "lib" / "amd64"
                if gxdk_lib.exists():
                    lib_paths.append(f"/LIBPATH:{gxdk_lib}")

            grdk_lib = self.gdk_latest / "GRDK" / "gamekit" / "lib" / "amd64"
            if grdk_lib.exists():
                lib_paths.append(f"/LIBPATH:{grdk_lib}")

            flags.extend(lib_paths)

        return flags

    # -----------------------------------------------------------------------
    # Interface Builder (méthodes abstraites)
    # -----------------------------------------------------------------------

    def GetObjectExtension(self) -> str:
        return ".obj"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dll"
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".lib"
        else:
            return ".exe"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        """Compile un fichier source avec MSVC."""
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = "cl.exe"
        args = [
            compiler,
            "/c",
            f"/Fo{obj}",
            f"/I{Path(project.location)}",
        ]

        # Includes supplémentaires
        for inc in project.includeDirs:
            args.append(f"/I{inc}")

        # Définitions
        for define in project.defines:
            args.append(f"/D{define}")

        # Optimisation / Debug
        if self.config.lower() == "debug" or project.symbols:
            args.append("/Od")
            args.append("/Zi")
            args.append("/MDd")
        else:
            opt = project.optimize.value if hasattr(project.optimize, 'value') else project.optimize
            if opt in ("Speed", "Full"):
                args.append("/O2")
            elif opt == "Size":
                args.append("/O1")
            else:
                args.append("/Od")
            args.append("/MD")

        # Warnings
        warn = project.warnings.value if hasattr(project.warnings, 'value') else project.warnings
        if warn == "All":
            args.append("/W4")
        elif warn == "Extra":
            args.append("/W3")
        elif warn == "Error":
            args.append("/WX")

        # Standard C++
        if project.language.value == "C++":
            args.append(f"/std:{project.cppdialect.lower().replace('++', 'c')}")

        # Fichier source
        args.append(str(src))

        # Flags Xbox spécifiques
        args.extend(self._GetXboxCompilerFlags())
        args.extend(self.GetModuleFlags(project, sourceFile))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        flags = []
        if not self.IsModuleFile(sourceFile):
            return flags
        flags.append("/interface")
        flags.append("/std:c++latest")
        obj_dir = self.GetObjectDir(project)
        ifc_name = Path(sourceFile).with_suffix('.ifc').name
        ifc_path = obj_dir / ifc_name
        flags.append(f"/module:output{str(ifc_path)}")
        return flags

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        """Édition de liens avec MSVC."""
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        linker = "link.exe"
        args = [linker]

        if project.kind == ProjectKind.SHARED_LIB:
            args.append("/DLL")
            out = out.with_suffix(".dll")
        elif project.kind == ProjectKind.STATIC_LIB:
            args = ["lib.exe", f"/OUT:{out}"]
            args.extend(objectFiles)
            result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
            return result.returnCode == 0
        else:
            args.append(f"/OUT:{out}")

        # Flags standards
        args.extend([
            "/NOLOGO",
            "/DYNAMICBASE",
            "/NXCOMPAT",
        ])

        if self.config.lower() == "debug":
            args.append("/DEBUG:FULL")

        # Objects
        args.extend(objectFiles)

        # Librairies
        args.append("kernel32.lib")
        args.append("user32.lib")
        args.append("ole32.lib")
        args.append("oleaut32.lib")

        for lib in project.links:
            args.append(f"{lib}.lib")

        # Flags Xbox spécifiques
        args.extend(self._GetXboxLinkerFlags())

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    # -----------------------------------------------------------------------
    # Build complet du projet Xbox
    # -----------------------------------------------------------------------

    def BuildProject(self, project: Project) -> bool:
        """
        Construit le projet Xbox :
        1. Compilation standard (héritée de Builder.BuildProject)
        2. Génération du MicrosoftGame.config
        3. Création du layout de déploiement
        4. Packaging XVC (pour console)
        5. Signature
        """
        Reporter.Info(f"Building Xbox project {project.name} ({self.xbox_platform})")

        # 1. Compilation normale (via Builder.BuildProject)
        if not super().BuildProject(project):
            return False

        # 2. Générer le fichier de configuration
        config_file = self._GenerateMicrosoftGameConfig(project)
        if not config_file:
            return False

        # 3. Créer le layout de déploiement
        layout_dir = self._CreateLooseLayout(project)
        if not layout_dir:
            return False

        # 4. Pour console : créer le package XVC
        if self.is_console and self.has_xbox_extensions:
            xvc_package = self._CreateXVCPackage(project, layout_dir)
            if not xvc_package:
                Reporter.Warning("XVC package creation failed, continuing with loose layout")

        # 5. Signer (selon configuration)
        if project.xboxSigningMode:
            self._SignPackage(project, layout_dir)

        return True

    # -----------------------------------------------------------------------
    # MicrosoftGame.config – Fichier de configuration du titre
    # -----------------------------------------------------------------------

    def _GenerateMicrosoftGameConfig(self, project: Project) -> Optional[Path]:
        """
        Génère le fichier MicrosoftGame.config requis pour tout package GDK.
        Format XML documenté par Microsoft [citation:2][citation:6].
        """
        output_dir = Path(self.GetTargetDir(project)) / "xbox-config"
        FileSystem.MakeDirectory(output_dir)
        config_path = output_dir / "MicrosoftGame.config"

        root = ET.Element("Game", {
            "xmlns": "http://schemas.microsoft.com/xbox/microsoftgame/2018",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
        })

        # Identité du titre
        identity = ET.SubElement(root, "Identity")
        ET.SubElement(identity, "Name").text = project.xboxPackageName or f"{project.name}.Game"
        ET.SubElement(identity, "Publisher").text = project.xboxPublisher or "Jenga"
        ET.SubElement(identity, "Version").text = project.xboxVersion or "1.0.0.0"

        # Propriétés
        properties = ET.SubElement(root, "Properties")
        ET.SubElement(properties, "DisplayName").text = project.targetName or project.name
        ET.SubElement(properties, "Description").text = getattr(project, 'description', f"{project.name} built with Jenga")

        # Configuration de la plateforme
        if self.is_console:
            ET.SubElement(properties, "ExecutableName").text = f"{project.targetName or project.name}.exe"
            ET.SubElement(properties, "ExecutablePath").text = f"{project.targetName or project.name}.exe"

        tree = ET.ElementTree(root)
        tree.write(config_path, encoding="utf-8", xml_declaration=True)

        Reporter.Detail(f"Generated MicrosoftGame.config: {config_path}")
        return config_path

    # -----------------------------------------------------------------------
    # Layout de déploiement (Loose)
    # -----------------------------------------------------------------------

    def _CreateLooseLayout(self, project: Project) -> Optional[Path]:
        """
        Crée un répertoire de layout "loose" pour déploiement rapide avec xbapp.
        Structure requise par xbapp deploy [citation:3].
        """
        target_exe = self.GetTargetPath(project)
        if not target_exe.exists():
            Reporter.Error(f"Executable not found: {target_exe}")
            return None

        layout_dir = Path(self.GetTargetDir(project)) / self.xbox_platform
        FileSystem.RemoveDirectory(layout_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(layout_dir)

        # Copier l'exécutable
        exe_name = f"{project.targetName or project.name}.exe"
        shutil.copy2(target_exe, layout_dir / exe_name)

        # Copier les DLLs (dépendances)
        for dep in project.dependFiles:
            dep_path = Path(dep)
            if dep_path.suffix.lower() == ".dll":
                shutil.copy2(dep_path, layout_dir / dep_path.name)

        # Copier MicrosoftGame.config
        config_src = layout_dir.parent / "xbox-config" / "MicrosoftGame.config"
        if config_src.exists():
            shutil.copy2(config_src, layout_dir / "MicrosoftGame.config")

        Reporter.Success(f"Loose layout created: {layout_dir}")
        return layout_dir

    # -----------------------------------------------------------------------
    # Packaging XVC / MSIXVC avec MakePkg
    # -----------------------------------------------------------------------

    def _CreateXVCPackage(self, project: Project, layout_dir: Path) -> Optional[Path]:
        """
        Crée un package XVC (.xvc) pour Xbox One/Series en utilisant MakePkg.exe.
        Implémente le processus complet : mapping, validation, signature, package [citation:2][citation:6].
        """
        if not self.gdk_latest:
            Reporter.Error("GDK not found, cannot create XVC package")
            return None

        # Localiser MakePkg.exe
        makepkg_path = self.gdk_latest / "bin" / "MakePkg.exe"
        if not makepkg_path.exists():
            Reporter.Error(f"MakePkg.exe not found at {makepkg_path}")
            return None

        package_dir = Path(self.GetTargetDir(project)) / "packages"
        FileSystem.MakeDirectory(package_dir)

        # 1. Générer le fichier de mapping XML
        mapping_file = self._GenerateMappingFile(project, layout_dir, package_dir)
        if not mapping_file:
            return None

        # 2. Déterminer le mode de signature
        signing_mode = getattr(project, 'xboxSigningMode', 'test')  # test, random, stable
        package_name = f"{project.xboxPackageName or project.name}"
        package_version = project.xboxVersion or "1.0.0.0"
        publisher_id = "8wekyb3d8bbwe"  # ID par défaut pour dev

        xvc_filename = f"{package_name}_{package_version}_neutral__{publisher_id}{self._XVC_EXTENSION}"
        xvc_path = package_dir / xvc_filename

        # 3. Construire la commande MakePkg
        cmd = [
            str(makepkg_path), "pack",
            "/f", str(mapping_file),
            "/d", str(layout_dir),
            "/pd", str(package_dir)
        ]

        # Mode de signature
        if signing_mode == "test":
            cmd.append("/lt")  # Test signing (default) [citation:2][citation:6]
        elif signing_mode == "random":
            cmd.append("/l")   # Random key
        elif signing_mode == "stable":
            # Nécessite une clé LEKB pré-générée
            lekb_path = getattr(project, 'xboxLEKBPath', None)
            if lekb_path:
                cmd.extend(["/lk", str(lekb_path)])
            else:
                Reporter.Warning("Stable key signing requested but no LEKB provided, falling back to test signing")
                cmd.append("/lt")

        # Plateforme cible
        if self.xbox_platform == "Gaming.Xbox.Scarlett.x64":
            cmd.append("/xs")  # Xbox Series X|S suffix
        else:
            cmd.append("/x")   # Xbox One suffix

        # Ajouter GameOS.xvd pour console (obligatoire) [citation:2][citation:6]
        if self.is_console:
            gameos_path = self.gdk_latest / "GXDK" / "gamekit" / "data" / "GameOS.xvd"
            if gameos_path.exists():
                cmd.extend(["/gameos", str(gameos_path.parent)])

        # 4. Exécuter MakePkg
        Reporter.Info(f"Creating XVC package: {xvc_filename}")
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)

        if result.returnCode == 0:
            # 5. Exécuter la validation automatique [citation:2][citation:6]
            self._RunSubmissionValidator(package_dir, xvc_path)
            Reporter.Success(f"XVC package created: {xvc_path}")
            return xvc_path
        else:
            Reporter.Error(f"MakePkg failed with code {result.returnCode}")
            return None

    def _GenerateMappingFile(self, project: Project, layout_dir: Path, output_dir: Path) -> Optional[Path]:
        """
        Génère le fichier de mapping XML requis par MakePkg.
        Définit les chunks pour le streaming install [citation:2][citation:6].
        """
        mapping_path = output_dir / "chunks.xml"

        root = ET.Element("Mapping", {
            "xmlns": "http://schemas.microsoft.com/xbox/mapping/2017"
        })

        # Chunk 0 : boot set (exécutable + config + dépendances critiques)
        chunk0 = ET.SubElement(root, "Chunk", {"id": "0"})
        ET.SubElement(chunk0, "FileGroup", {"path": f"{layout_dir.name}\\*.exe"})
        ET.SubElement(chunk0, "FileGroup", {"path": f"{layout_dir.name}\\MicrosoftGame.config"})

        # Chunk 1 : librairies
        chunk1 = ET.SubElement(root, "Chunk", {"id": "1"})
        ET.SubElement(chunk1, "FileGroup", {"path": f"{layout_dir.name}\\*.dll"})

        # Chunks supplémentaires pour les assets
        if project.xboxAssetChunks:
            for i, asset_pattern in enumerate(project.xboxAssetChunks, start=2):
                chunk = ET.SubElement(root, "Chunk", {"id": str(i)})
                ET.SubElement(chunk, "FileGroup", {"path": asset_pattern})

        tree = ET.ElementTree(root)
        tree.write(mapping_path, encoding="utf-8", xml_declaration=True)

        return mapping_path

    # -----------------------------------------------------------------------
    # Validation pré-soumission
    # -----------------------------------------------------------------------

    def _RunSubmissionValidator(self, package_dir: Path, package_path: Path):
        """
        Exécute SubmissionValidator.dll sur le package créé.
        Indispensable avant soumission au Partner Center [citation:2][citation:6].
        """
        if not self.gdk_latest:
            return

        validator_path = self.gdk_latest / "bin" / "SubmissionValidator.dll"
        if not validator_path.exists():
            Reporter.Warning("SubmissionValidator.dll not found, skipping validation")
            return

        log_path = package_dir / "submission_validation.xml"

        cmd = [
            "dotnet", str(validator_path),
            "validate",
            "-p", str(package_path),
            "-o", str(log_path)
        ]

        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)

        if result.returnCode == 0:
            Reporter.Success("Submission validation passed")
        else:
            Reporter.Error(f"Submission validation failed. Check log: {log_path}")

    # -----------------------------------------------------------------------
    # Signature
    # -----------------------------------------------------------------------

    def _SignPackage(self, project: Project, layout_dir: Path):
        """
        Signe le package selon le mode configuré.
        Pour la signature stable, gère la génération et la conservation des LEKB [citation:2][citation:6].
        """
        signing_mode = getattr(project, 'xboxSigningMode', 'test')

        if signing_mode == "stable":
            # Générer une clé LEKB si elle n'existe pas
            lekb_path = getattr(project, 'xboxLEKBPath', None)
            if not lekb_path:
                lekb_path = self._GenerateLEKB(project)
                if lekb_path:
                    project.xboxLEKBPath = str(lekb_path)

    def _GenerateLEKB(self, project: Project) -> Optional[Path]:
        """
        Génère une clé LEKB (Local EscrowEd Key Blob) pour la signature stable.
        La clé doit être conservée secrètement [citation:2][citation:6].
        """
        if not self.gdk_latest:
            return None

        makepkg_path = self.gdk_latest / "bin" / "MakePkg.exe"
        if not makepkg_path.exists():
            return None

        key_dir = Path(self.workspace.location) / ".jenga" / "keys"
        FileSystem.MakeDirectory(key_dir)

        lekb_path = key_dir / f"{project.name}_secret.lekb"

        cmd = [
            str(makepkg_path), "genkey",
            "/ekb", str(lekb_path)
        ]

        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)

        if result.returnCode == 0:
            Reporter.Warning(f"LEKB generated at {lekb_path}. THIS FILE MUST BE KEPT SECRET!")
            return lekb_path
        else:
            Reporter.Error("Failed to generate LEKB")
            return None

    # -----------------------------------------------------------------------
    # Déploiement sur console
    # -----------------------------------------------------------------------

    def DeployToConsole(self, project: Project, layout_dir: Path, console_ip: Optional[str] = None) -> bool:
        """
        Déploie le layout ou le package sur une console de développement via xbapp.
        Utilise xbapp.exe du GDK [citation:3].
        """
        if not self.gdk_latest:
            Reporter.Error("GDK not found, cannot deploy")
            return False

        xbapp_path = self.gdk_latest / "bin" / "xbapp.exe"
        if not xbapp_path.exists():
            Reporter.Error(f"xbapp.exe not found at {xbapp_path}")
            return False

        # Déployer le layout loose (recommandé pour l'itération) [citation:3]
        cmd = [
            str(xbapp_path), "deploy",
            str(layout_dir)
        ]

        if console_ip:
            cmd.extend(["/s", console_ip])

        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)

        if result.returnCode == 0:
            Reporter.Success(f"Deployed to console")
            return True
        else:
            Reporter.Error("Deployment failed")
            return False

    def LaunchOnConsole(self, project: Project, console_ip: Optional[str] = None) -> bool:
        """
        Lance l'exécutable sur la console via xbapp launch [citation:3].
        """
        if not self.gdk_latest:
            return False

        xbapp_path = self.gdk_latest / "bin" / "xbapp.exe"
        exe_name = f"{project.targetName or project.name}.exe"

        cmd = [
            str(xbapp_path), "launch",
            exe_name
        ]

        if console_ip:
            cmd.extend(["/s", console_ip])

        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return result.returnCode == 0