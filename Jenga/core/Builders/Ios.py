#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS Builder – Compilation pour iOS et simulateur sans Xcode.
Utilise directement Apple Clang via les outils en ligne de commande.
Génère des .a, .dylib (expérimental) et des bundles .app.
Support des modules C++20 (Clang -fmodules).
Signe les bundles pour périphérique réel.
"""

import os
import sys
import shutil
import plistlib
import json
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from Jenga.Core.Api import Project, ProjectKind, TargetArch, CompilerFamily
from ...Utils import Process, FileSystem, Colored, Reporter
from ..Builder import Builder
from ..Platform import Platform


class IOSBuilder(Builder):
    """
    Builder iOS pur, sans xcodebuild.
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)

        # Déterminer si c'est le simulateur ou périphérique réel
        self.is_simulator = (self.targetArch in (TargetArch.X86_64, TargetArch.X86))
        self.sdk_name = "iphonesimulator" if self.is_simulator else "iphoneos"

        # Récupérer le chemin du SDK via xcrun
        self.sdk_path = self._GetSDKPath(self.sdk_name)
        if not self.sdk_path:
            raise RuntimeError(f"iOS SDK '{self.sdk_name}' not found. Install Xcode command line tools.")

        # Vérifier que le compilateur est AppleClang
        self._CheckCompiler()

        # Version minimale iOS
        self.min_version = self._GetMinimumVersion()

        # Cible (target triple)
        self.target_triple = self._GetTargetTriple()

    # -----------------------------------------------------------------------
    # Détection de l'environnement Apple
    # -----------------------------------------------------------------------

    def _GetSDKPath(self, sdk: str) -> Optional[Path]:
        """Retourne le chemin du SDK via xcrun."""
        try:
            result = Process.Capture(["xcrun", "--sdk", sdk, "--show-sdk-path"])
            return Path(result.strip())
        except Exception as e:
            Colored.PrintError(f"Failed to get SDK path for {sdk}: {e}")
            return None

    def _CheckCompiler(self):
        """Vérifie que le compilateur disponible est AppleClang."""
        # On utilise xcrun pour trouver clang
        try:
            cc_path = Process.Capture(["xcrun", "--find", "clang"]).strip()
            cxx_path = Process.Capture(["xcrun", "--find", "clang++"]).strip()
            self.toolchain.ccPath = cc_path
            self.toolchain.cxxPath = cxx_path
            self.toolchain.compilerFamily = CompilerFamily.APPLE_CLANG
        except Exception as e:
            raise RuntimeError(f"Apple Clang not found. Install Xcode command line tools: {e}")

    def _GetMinimumVersion(self) -> str:
        """Détermine la version minimale iOS depuis le projet ou défaut."""
        # Cherche dans le premier projet iOS (ou utilise 12.0)
        for proj in self.workspace.projects.values():
            if hasattr(proj, 'iosMinSdk') and proj.iosMinSdk:
                return proj.iosMinSdk
        return "12.0"

    def _GetTargetTriple(self) -> str:
        """Construit le triplet cible (ex: arm64-apple-ios12.0-simulator)."""
        arch = "arm64" if self.targetArch == TargetArch.ARM64 else "x86_64"
        os_part = "ios"
        version = self.min_version
        suffix = "-simulator" if self.is_simulator else ""
        return f"{arch}-apple-{os_part}{version}{suffix}"

    # -----------------------------------------------------------------------
    # Implémentation des méthodes abstraites
    # -----------------------------------------------------------------------

    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"      # iOS permet les dylibs embarquées, mais rare
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        else:
            return ".app"        # Bundle pour exécutable

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        """
        Flags pour modules C++20 (AppleClang supporte -fmodules).
        """
        flags = []
        if not self.IsModuleFile(sourceFile):
            return flags

        flags.append("-fmodules")
        flags.append("-fcxx-modules")
        flags.append("-fbuiltin-module-map")
        flags.append(f"-target {self.target_triple}")
        flags.append(f"-isysroot {self.sdk_path}")
        flags.append(f"-mios-version-min={self.min_version}")
        # Clang génère automatiquement les .pcm dans le répertoire des objets
        return flags

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        """
        Compile un fichier source avec Apple Clang.
        """
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        # Déterminer le compilateur C ou C++
        if project.language.value in ("C++", "Objective-C++"):
            compiler = self.toolchain.cxxPath
        else:
            compiler = self.toolchain.ccPath

        args = [
            compiler,
            "-c",
            "-o", str(obj),
            *self.GetDependencyFlags(str(obj)),
            f"-target", self.target_triple,
            f"-isysroot", str(self.sdk_path),
            f"-mios-version-min={self.min_version}",
        ]

        # Architecture explicite (redondant avec target, mais sûr)
        arch = "arm64" if self.targetArch == TargetArch.ARM64 else "x86_64"
        args.extend(["-arch", arch])

        # Flags généraux (includes, defines, optimisation, warnings)
        args.extend(self._GetCompilerFlags(project))

        # Modules C++20
        if self.IsModuleFile(sourceFile):
            args.extend(self.GetModuleFlags(project, sourceFile))

        # Fichier source
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        """
        Édition des liens.
        - Pour static lib : utilise libtool (ar)
        - Pour executable : link + création du bundle .app
        """
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            return self._LinkStaticLib(project, objectFiles, out)
        else:
            # Exécutable
            executable = out.parent / (project.targetName or project.name)
            if not self._LinkExecutable(project, objectFiles, executable):
                return False
            # Créer le bundle .app
            app_bundle = self._CreateAppBundle(project, executable)
            if not app_bundle:
                return False
            # Codesigner si nécessaire
            if not self.is_simulator and project.iosSigningIdentity:
                if not self._Codesign(app_bundle, project):
                    return False
            # Lier le fichier de sortie symbolique (optionnel)
            # On crée un lien symbolique du bundle vers outputFile pour compatibilité
            if outputFile.endswith('.app'):
                shutil.rmtree(outputFile, ignore_errors=True)
                os.symlink(app_bundle, outputFile, target_is_directory=True)
            return True

    def _LinkStaticLib(self, project: Project, objectFiles: List[str], output: Path) -> bool:
        """Crée une bibliothèque statique .a avec libtool."""
        # Sur macOS/iOS, libtool -static est l'équivalent de ar
        args = ["libtool", "-static", "-o", str(output)] + objectFiles
        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def _LinkExecutable(self, project: Project, objectFiles: List[str], output: Path) -> bool:
        """Link l'exécutable."""
        linker = self.toolchain.cxxPath
        args = [
            linker,
            "-o", str(output),
            f"-target", self.target_triple,
            f"-isysroot", str(self.sdk_path),
            f"-mios-version-min={self.min_version}",
        ]
        arch = "arm64" if self.targetArch == TargetArch.ARM64 else "x86_64"
        args.extend(["-arch", arch])

        # Frameworks standards
        args.extend(["-framework", "Foundation"])
        args.extend(["-framework", "UIKit"])
        if not self.is_simulator:
            args.extend(["-framework", "OpenGLES"])

        # Librairies
        for libdir in project.libDirs:
            args.append(f"-L{libdir}")
        for lib in project.links:
            args.append(f"-l{lib}")

        args.extend(objectFiles)

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    # -----------------------------------------------------------------------
    # Création du bundle .app
    # -----------------------------------------------------------------------

    def _CreateAppBundle(self, project: Project, executable: Path) -> Optional[Path]:
        """
        Crée la structure d'un bundle .app selon les spécifications Apple.
        https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html
        """
        app_name = project.targetName or project.name
        bundle_dir = executable.parent / f"{app_name}.app"
        FileSystem.RemoveDirectory(bundle_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(bundle_dir)

        # Copier l'exécutable dans le bundle
        dest_exe = bundle_dir / app_name
        shutil.copy2(executable, dest_exe)

        # Copier les éventuelles ressources
        for pattern in project.embedResources:
            base_dir = Path(project.location) if project.location else Path.cwd()
            for f in FileSystem.ListFiles(base_dir, pattern, recursive=True, fullPath=True):
                dest = bundle_dir / Path(f).relative_to(base_dir)
                FileSystem.MakeDirectory(dest.parent)
                shutil.copy2(f, dest)

        # Générer Info.plist
        info_plist = self._GenerateInfoPlist(project, bundle_dir)
        if info_plist:
            shutil.copy2(info_plist, bundle_dir / "Info.plist")

        # Copier l'icône si spécifiée
        if project.iosAppIcon:
            icon_path = Path(project.iosAppIcon)
            if icon_path.exists():
                shutil.copy2(icon_path, bundle_dir / icon_path.name)

        return bundle_dir

    def _GenerateInfoPlist(self, project: Project, bundle_dir: Path) -> Optional[Path]:
        """
        Génère un Info.plist valide.
        Se référer à [citation:1] pour les erreurs à éviter.
        """
        app_name = project.targetName or project.name
        bundle_id = project.iosBundleId or f"com.{project.name}.app"

        plist = {
            "CFBundleName": app_name,
            "CFBundleDisplayName": app_name,
            "CFBundleIdentifier": bundle_id,
            "CFBundleVersion": project.iosBuildNumber or "1",
            "CFBundleShortVersionString": project.iosVersion or "1.0",
            "CFBundleExecutable": app_name,
            "CFBundlePackageType": "APPL",           # [citation:1] obligatoire pour Transporter
            "CFBundleSupportedPlatforms": ["iPhoneOS"] if not self.is_simulator else ["iPhoneSimulator"],
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundleDevelopmentRegion": "en",
            "LSRequiresIPhoneOS": True,
            "UISupportedInterfaceOrientations": [
                "UIInterfaceOrientationPortrait",
                "UIInterfaceOrientationLandscapeLeft",
                "UIInterfaceOrientationLandscapeRight"
            ],
            "UISupportedInterfaceOrientations~ipad": [
                "UIInterfaceOrientationPortrait",
                "UIInterfaceOrientationPortraitUpsideDown",
                "UIInterfaceOrientationLandscapeLeft",
                "UIInterfaceOrientationLandscapeRight"
            ],
            "LSMinimumSystemVersion": self.min_version,   # [citation:1] requis pour Mac App Store, mais aussi pour iOS?
            "UIDeviceFamily": [1, 2],                    # 1=iPhone, 2=iPad
        }

        # Ajouter la clé d'icône si présente
        if project.iosAppIcon:
            plist["CFBundleIconFile"] = Path(project.iosAppIcon).name

        plist_path = bundle_dir / "Info.plist"
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist, f)
        return plist_path

    # -----------------------------------------------------------------------
    # Signature de code (codesign)
    # -----------------------------------------------------------------------

    def _Codesign(self, bundle_path: Path, project: Project) -> bool:
        """
        Signe le bundle avec l'identité spécifiée.
        Utilise la commande `codesign`.
        """
        identity = project.iosSigningIdentity
        if not identity:
            # Chercher une identité par défaut
            identity = self._GetDefaultSigningIdentity()
            if not identity:
                Colored.PrintWarning("No code signing identity found. Skipping codesign.")
                return True

        entitlements = self._GenerateEntitlements(project, bundle_path)

        args = [
            "codesign",
            "--force",
            "--sign", identity,
            "--timestamp",
            "--verbose",
            "--options", "runtime",
        ]
        if entitlements:
            args.extend(["--entitlements", str(entitlements)])
        args.append(str(bundle_path))

        result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
        if result.returnCode != 0:
            Colored.PrintError(f"Code signing failed for {bundle_path}")
            return False
        return True

    def _GetDefaultSigningIdentity(self) -> Optional[str]:
        """Récupère la première identité de signature valide (Developer ID ou Apple Development)."""
        try:
            output = Process.Capture(["security", "find-identity", "-v", "-p", "codesigning"])
            for line in output.splitlines():
                if "Developer ID Application:" in line or "Apple Development:" in line:
                    # Extrait le texte entre guillemets
                    import re
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        return match.group(1)
        except Exception:
            pass
        return None

    def _GenerateEntitlements(self, project: Project, bundle_dir: Path) -> Optional[Path]:
        """
        Génère un fichier entitlements.plist si nécessaire.
        """
        # Pour l'instant, on ne génère rien par défaut.
        # L'utilisateur peut spécifier un fichier .entitlements via project.iosEntitlements
        if hasattr(project, 'iosEntitlements') and project.iosEntitlements:
            src = Path(project.iosEntitlements)
            if src.exists():
                dst = bundle_dir / ".." / "Entitlements.plist"
                shutil.copy2(src, dst)
                return dst
        return None

    # -----------------------------------------------------------------------
    # Flags de compilation communs
    # -----------------------------------------------------------------------

    def _GetCompilerFlags(self, project: Project) -> List[str]:
        flags = []

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{inc}")

        # Définitions
        for define in project.defines:
            flags.append(f"-D{define}")
        flags.append("-DIOS")
        if self.is_simulator:
            flags.append("-D__SIMULATOR__")

        # Debug symbols
        if project.symbols:
            flags.append("-g")

        # Optimisation
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
        elif warn == "Everything":
            flags.append("-Weverything")
        elif warn == "Error":
            flags.append("-Werror")

        # Standard
        if project.language.value in ("C++", "Objective-C++"):
            flags.append(f"-std={project.cppdialect.lower()}")
        else:
            flags.append(f"-std={project.cdialect.lower()}")
        if project.language.value in ("Objective-C", "Objective-C++"):
            flags.append("-ObjC++")

        # Flags spécifiques iOS
        flags.append(f"-target {self.target_triple}")
        flags.append(f"-isysroot {self.sdk_path}")
        flags.append(f"-mios-version-min={self.min_version}")

        return flags

    # -----------------------------------------------------------------------
    # Build complet (override de BuildProject si nécessaire)
    # -----------------------------------------------------------------------

    def BuildProject(self, project: Project) -> bool:
        """
        Construction complète d'un projet iOS.
        Utilise la logique de compilation/link héritée de Builder,
        mais nous avons surchargé Compile et Link.
        """
        # Vérifier que l'hôte est macOS
        if Platform.GetHostOS() != Platform.TargetOS.MACOS:
            raise RuntimeError("iOS builds require macOS with Xcode command line tools.")

        return super().BuildProject(project)
