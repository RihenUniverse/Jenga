#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android Builder – Compilation pour Android via NDK.
Gère les bibliothèques natives (.so), packaging APK/AAB, signature.
Support complet : armeabi-v7a, arm64-v8a, x86, x86_64.
Ajoute la compilation Java (via androidJavaFiles), les bibliothèques Java (.jar via androidJavaLibs),
ProGuard/R8, les exécutables console, et le support complet des Android App Bundles (AAB).
"""

import os
import shutil
import xml.etree.ElementTree as ET
import zipfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Set
import tempfile, sys
import glob
import fnmatch

from Jenga.Core.Api import Project, ProjectKind, TargetArch, TargetOS
from ...Utils import Process, FileSystem, Colored, Reporter
from ..Builder import Builder
from ..Toolchains import ToolchainManager


class AndroidBuilder(Builder):
    """
    Builder pour Android.
    Supporte :
      - Compilation NDK (C/C++)
      - Compilation Java (si sources présentes via androidJavaFiles)
      - Packaging APK signé (debug/release) avec ou sans code Java
      - Packaging AAB (Android App Bundle)
      - ProGuard / R8 (optionnel)
      - Exécutables console (binaires ELF)
      - Assets et ressources multi-dossiers
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False,
                 action: str = "build", options: Optional[List[str]] = None):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose, action=action, options=options)

        # Résolution des chemins SDK/NDK/JDK
        self.sdk_path = self._ResolveSDKPath()
        self.ndk_path = self._ResolveNDKPath()
        self.jdk_path = self._ResolveJDKPath()

        if not self.ndk_path:
            raise RuntimeError("Android NDK not found. Set androidNdkPath in workspace or ANDROID_NDK_ROOT env var.")
        if not self.sdk_path:
            raise RuntimeError("Android SDK not found. Set androidSdkPath in workspace or ANDROID_SDK_ROOT env var.")

        self.build_tools = self._GetLatestBuildTools()
        self.aapt2 = self._ToolPath("aapt2")
        self.apksigner = self._ToolPath("apksigner")
        self.zipalign = self._ToolPath("zipalign")
        self.d8 = self._ToolPath("d8")  # ou d8.jar selon version

        self.platform_jar = self.sdk_path / "platforms" / f"android-{self._GetTargetSdkVersion()}" / "android.jar"
        if not self.platform_jar.exists():
            # Fallback: version la plus haute disponible
            platforms = sorted([p for p in (self.sdk_path / "platforms").glob("android-*")], reverse=True)
            if platforms:
                self.platform_jar = platforms[0] / "android.jar"

        # Configurer la toolchain NDK pour l'architecture cible
        self._PrepareNDKToolchain()

        # Options de build
        self.build_aab = self._OptionEnabled("aab") or self._OptionEnabled("bundle")
        self.use_proguard = self._OptionEnabled("proguard") or self._OptionEnabled("r8")

        # Chemins pour ProGuard
        self.proguard_jar = self._FindProguardJar()

    # -----------------------------------------------------------------------
    # Résolution des chemins SDK/NDK/JDK (inchangé)
    # -----------------------------------------------------------------------

    def _ResolveSDKPath(self) -> Optional[Path]:
        """Détermine le chemin du SDK Android."""
        if self.workspace.androidSdkPath:
            return Path(self.workspace.androidSdkPath).resolve()
        if "ANDROID_SDK_ROOT" in os.environ:
            return Path(os.environ["ANDROID_SDK_ROOT"])
        if "ANDROID_HOME" in os.environ:
            return Path(os.environ["ANDROID_HOME"])
        # Chemins par défaut
        if sys.platform == "win32":
            candidates = [Path("C:/Users") / os.getlogin() / "AppData/Local/Android/Sdk"]
        elif sys.platform == "darwin":
            candidates = [Path.home() / "Library/Android/sdk"]
        else:
            candidates = [Path.home() / "Android/Sdk"]
        for cand in candidates:
            if cand.exists():
                return cand
        return None

    def _ResolveNDKPath(self) -> Optional[Path]:
        """Détermine le chemin du NDK Android."""
        if self.workspace.androidNdkPath:
            return Path(self.workspace.androidNdkPath).resolve()
        if "ANDROID_NDK_ROOT" in os.environ:
            return Path(os.environ["ANDROID_NDK_ROOT"])
        if "ANDROID_NDK_HOME" in os.environ:
            return Path(os.environ["ANDROID_NDK_HOME"])
        # Si SDK trouvé, chercher ndk-bundle
        if self.sdk_path:
            ndk_bundle = self.sdk_path / "ndk-bundle"
            if ndk_bundle.exists():
                return ndk_bundle
            # Chercher des versions spécifiques
            ndk_dir = self.sdk_path / "ndk"
            if ndk_dir.exists():
                versions = sorted(ndk_dir.iterdir(), reverse=True)
                if versions:
                    return versions[0]
        return None

    def _ResolveJDKPath(self) -> Optional[Path]:
        """Détermine le chemin du JDK (nécessaire pour d8, apksigner)."""
        if self.workspace.javaJdkPath:
            return Path(self.workspace.javaJdkPath).resolve()
        if "JAVA_HOME" in os.environ:
            return Path(os.environ["JAVA_HOME"])
        # Fallback: essayer de trouver java dans PATH
        java = Process.Which("java")
        if java:
            return Path(java).parent.parent
        return None

    def _GetLatestBuildTools(self) -> Path:
        """Retourne le chemin du dossier build-tools le plus récent."""
        bt_dir = self.sdk_path / "build-tools"
        if not bt_dir.exists():
            raise RuntimeError(f"build-tools not found in SDK: {bt_dir}")
        versions = sorted([d for d in bt_dir.iterdir() if d.is_dir()], key=lambda p: p.name, reverse=True)
        if not versions:
            raise RuntimeError("No build-tools version found")
        return versions[0]

    def _ToolPath(self, name: str) -> Path:
        """Resolve build-tools executable path across OSes."""
        if sys.platform == "win32":
            for ext in (".exe", ".bat", ".cmd"):
                cand = self.build_tools / f"{name}{ext}"
                if cand.exists():
                    return cand
        cand = self.build_tools / name
        if cand.exists():
            return cand
        return cand

    def _GetTargetSdkVersion(self) -> int:
        """Récupère la version targetSdk depuis le premier projet ou workspace."""
        # On prend le plus haut targetSdk parmi les projets, ou 33 par défaut
        max_sdk = 33
        for proj in self.workspace.projects.values():
            if hasattr(proj, 'androidTargetSdk') and proj.androidTargetSdk:
                max_sdk = max(max_sdk, proj.androidTargetSdk)
        return max_sdk

    # -----------------------------------------------------------------------
    # Configuration NDK (inchangé)
    # -----------------------------------------------------------------------

    def _PrepareNDKToolchain(self):
        """Configure la toolchain NDK pour l'architecture cible."""
        # Le NDK fournit une toolchain clang préconstruite
        host_tag = {
            "win32": "windows-x86_64",
            "linux": "linux-x86_64",
            "darwin": "darwin-x86_64"
        }.get(sys.platform, "linux-x86_64")

        llvm_dir = self.ndk_path / "toolchains" / "llvm" / "prebuilt" / host_tag
        if not llvm_dir.exists():
            raise RuntimeError(f"LLVM toolchain not found in NDK: {llvm_dir}")

        # Architecture -> triplet et ABI
        arch_info = {
            TargetArch.ARM: {
                "triple": "armv7a-linux-androideabi",
                "abi": "armeabi-v7a",
                "llvm_triple": "armv7a-linux-androideabi"
            },
            TargetArch.ARM64: {
                "triple": "aarch64-linux-android",
                "abi": "arm64-v8a",
                "llvm_triple": "aarch64-linux-android"
            },
            TargetArch.X86: {
                "triple": "i686-linux-android",
                "abi": "x86",
                "llvm_triple": "i686-linux-android"
            },
            TargetArch.X86_64: {
                "triple": "x86_64-linux-android",
                "abi": "x86_64",
                "llvm_triple": "x86_64-linux-android"
            }
        }.get(self.targetArch)

        if not arch_info:
            raise RuntimeError(f"Unsupported Android architecture: {self.targetArch}")

        self.ndk_triple = arch_info["triple"]
        self.ndk_abi = arch_info["abi"]
        self.ndk_llvm_triple = arch_info["llvm_triple"]

        # Mettre à jour la toolchain avec les chemins NDK
        if self.toolchain:
            self.toolchain.ccPath = str(llvm_dir / "bin" / "clang")
            self.toolchain.cxxPath = str(llvm_dir / "bin" / "clang++")
            self.toolchain.arPath = str(llvm_dir / "bin" / "llvm-ar")
            self.toolchain.ldPath = str(llvm_dir / "bin" / "ld")
            self.toolchain.stripPath = str(llvm_dir / "bin" / "llvm-strip")
            self.toolchain.ranlibPath = str(llvm_dir / "bin" / "llvm-ranlib")
            self.toolchain.toolchainDir = str(llvm_dir)
            self.toolchain.sysroot = str(llvm_dir / "sysroot")
            # Target triplet par défaut
            self.toolchain.targetTriple = f"{self.ndk_triple}{self._GetMinApiLevel()}"

    def _GetMinApiLevel(self) -> int:
        """Récupère le niveau d'API minimum pour le projet principal."""
        # Cherche dans le premier projet Android, sinon 21
        for proj in self.workspace.projects.values():
            if proj.kind in (ProjectKind.CONSOLE_APP, ProjectKind.SHARED_LIB) and proj.targetOs == TargetOS.ANDROID:
                return proj.androidMinSdk or 21
        return 21

    # -----------------------------------------------------------------------
    # Compilation native (inchangé sauf pour exécutables)
    # -----------------------------------------------------------------------

    def GetObjectExtension(self) -> str:
        return ".o"

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        p = Path(lib)
        return p.suffix in (".a", ".so", ".dylib", ".lib") or "/" in lib or "\\" in lib or p.is_absolute()

    def PreparePCH(self, project: Project, objDir: Path) -> bool:
        project._jengaPchFile = ""
        project._jengaPchHeaderResolved = ""
        project._jengaPchSourceResolved = ""
        if not project.pchHeader:
            return True
        header = Path(self.ResolveProjectPath(project, project.pchHeader))
        if not header.exists():
            return False
        compiler = self.toolchain.cxxPath or self.toolchain.ccPath
        pch_path = objDir / f"{project.name}.pch"
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
        if project.kind == ProjectKind.SHARED_LIB:
            return ".so"
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        elif project.kind == ProjectKind.CONSOLE_APP:
            # Les exécutables Android n'ont pas d'extension
            return ""
        else:  # WINDOWED_APP
            return ".so"  # les applications graphiques sont des .so avec NativeActivity

    def GetTargetPath(self, project: Project) -> Path:
        target_dir = self.GetTargetDir(project)
        target_name = project.targetName or project.name
        ext = self.GetOutputExtension(project)
        if project.kind in (ProjectKind.WINDOWED_APP, ProjectKind.SHARED_LIB):
            if not target_name.startswith("lib"):
                target_name = f"lib{target_name}"
        elif project.kind == ProjectKind.STATIC_LIB:
            if not target_name.startswith("lib"):
                target_name = f"lib{target_name}"
        # Pour les exécutables console, pas de préfixe lib
        return target_dir / f"{target_name}{ext}"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [compiler, "-c", "-o", str(obj)]
        args.extend(self.GetDependencyFlags(str(obj)))
        args.extend(self._GetCompilerFlags(project))
        if self.IsModuleFile(sourceFile):
            args.extend(self.GetModuleFlags(project, sourceFile))
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def _BuildNativeAppGlueObject(self, project: Project, obj_dir: Path) -> Optional[str]:
        """Compile android_native_app_glue.c from NDK sources for NativeActivity apps."""
        if not project.androidNativeActivity:
            return None
        glue_src = self.ndk_path / "sources" / "android" / "native_app_glue" / "android_native_app_glue.c"
        if not glue_src.exists():
            return None
        glue_inc = self.ndk_path / "sources" / "android" / "native_app_glue"
        glue_obj = obj_dir / "android_native_app_glue.o"
        compiler = self.toolchain.ccPath or self.toolchain.cxxPath
        if not compiler:
            return None
        min_api = project.androidMinSdk or 21
        target = f"{self.ndk_llvm_triple}{min_api}"
        args = [
            compiler,
            "--target=" + target,
            "--sysroot=" + str(self.toolchain.sysroot),
            "-I" + str(glue_inc),
            "-DANDROID",
            "-fPIC",
            "-std=c11",
            "-c", str(glue_src),
            "-o", str(glue_obj),
        ]
        if project.symbols:
            args.append("-g")
        opt = project.optimize.value if hasattr(project.optimize, 'value') else project.optimize
        if opt == "Off":
            args.append("-O0")
        elif opt == "Size":
            args.append("-Os")
        elif opt == "Speed":
            args.append("-O2")
        elif opt == "Full":
            args.append("-O3")
        if self.targetArch == TargetArch.ARM:
            args.extend(["-march=armv7-a", "-mfloat-abi=softfp", "-mfpu=vfpv3-d16"])
        elif self.targetArch == TargetArch.ARM64:
            args.append("-march=armv8-a")
        elif self.targetArch == TargetArch.X86:
            args.append("-march=i686")
        elif self.targetArch == TargetArch.X86_64:
            args.append("-march=x86-64")
        result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
        if result.returnCode != 0:
            return None
        return str(glue_obj)
    
    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        flags = []
        if not self.IsModuleFile(sourceFile):
            return flags

        # Clang dans NDK supporte -fmodules
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
            ar = self.toolchain.arPath or "llvm-ar"
            args = [ar, "rcs", str(out)]
            args.extend(objectFiles)
            result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
            return result.returnCode == 0
        else:
            linker = self.toolchain.cxxPath
            # Déterminer si on crée un exécutable ou une bibliothèque partagée
            if project.kind == ProjectKind.CONSOLE_APP:
                link_type = []  # exécutable par défaut (pas de -shared)
            else:
                link_type = ["-shared"]  # bibliothèque partagée pour WINDOWED_APP et SHARED_LIB
            args = [linker] + link_type + ["-o", str(out)]
            args.extend(self._GetLinkerFlags(project))
            # Object files first; archives are order-sensitive.
            final_objects = list(objectFiles)
            if project.androidNativeActivity and project.kind != ProjectKind.CONSOLE_APP:
                glue_obj = self._BuildNativeAppGlueObject(project, self.GetObjectDir(project))
                if not glue_obj:
                    Colored.PrintError("android_native_app_glue source not found/compilation failed in NDK")
                    return False
                final_objects.append(glue_obj)
            args.extend(final_objects)
            for libdir in project.libDirs:
                args.append(f"-L{self.ResolveProjectPath(project, libdir)}")
            for lib in project.links:
                if self._IsDirectLibPath(lib):
                    args.append(self.ResolveProjectPath(project, lib))
                else:
                    args.append(f"-l{lib}")
            # Pour les exécutables, il faut inclure crtbegin_dynamic.o et crtend_android.o
            if project.kind == ProjectKind.CONSOLE_APP:
                # Ajouter les objets de démarrage NDK
                min_api = project.androidMinSdk or 21
                arch_lib = Path(self.toolchain.sysroot) / "usr" / "lib" / self.ndk_triple / str(min_api)
                crtbegin = arch_lib / "crtbegin_dynamic.o"
                crtend = arch_lib / "crtend_android.o"
                if crtbegin.exists():
                    # Réorganiser les arguments pour placer crtbegin avant les objets et crtend après
                    # On reconstruit la commande
                    args = [linker] + link_type + ["-o", str(out)] + [str(crtbegin)] + final_objects + [str(crtend)]
                    # Ajouter les flags de librairies et autres
                    for libdir in project.libDirs:
                        args.append(f"-L{self.ResolveProjectPath(project, libdir)}")
                    for lib in project.links:
                        if self._IsDirectLibPath(lib):
                            args.append(self.ResolveProjectPath(project, lib))
                        else:
                            args.append(f"-l{lib}")
                else:
                    Colored.PrintWarning(f"crtbegin_dynamic.o not found for API {min_api}, linking may fail")
            result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
            return result.returnCode == 0

    def _GetCompilerFlags(self, project: Project) -> List[str]:
        flags = []

        # Target triple
        min_api = project.androidMinSdk or 21
        target = f"{self.ndk_llvm_triple}{min_api}"
        flags.append(f"--target={target}")

        # Sysroot
        flags.append(f"--sysroot={self.toolchain.sysroot}")

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{self.ResolveProjectPath(project, inc)}")
        pch_file = getattr(project, "_jengaPchFile", "")
        if pch_file:
            flags.extend(["-include-pch", pch_file])

        # Définitions
        for define in project.defines:
            flags.append(f"-D{define}")
        flags.append("-DANDROID")
        if project.androidNativeActivity and project.kind != ProjectKind.CONSOLE_APP:
            glue_inc = self.ndk_path / "sources" / "android" / "native_app_glue"
            if glue_inc.exists():
                flags.append(f"-I{glue_inc}")

        # Debug / Optimisation
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

        # PIC sauf pour les exécutables
        if project.kind != ProjectKind.CONSOLE_APP:
            flags.append("-fPIC")
        else:
            flags.append("-fPIE")  # Position Independent Executable

        # Architecture spécifique
        if self.targetArch == TargetArch.ARM:
            flags.extend(["-march=armv7-a", "-mfloat-abi=softfp", "-mfpu=vfpv3-d16"])
        elif self.targetArch == TargetArch.ARM64:
            flags.append("-march=armv8-a")
        elif self.targetArch == TargetArch.X86:
            flags.append("-march=i686")
        elif self.targetArch == TargetArch.X86_64:
            flags.append("-march=x86-64")

        # Flags supplémentaires du projet
        if project.language.value in ("C++", "Objective-C++"):
            flags.extend(project.cxxflags)
        else:
            flags.extend(project.cflags)

        return flags

    def _GetLinkerFlags(self, project: Project) -> List[str]:
        flags = []

        # Target et sysroot
        min_api = project.androidMinSdk or 21
        target = f"{self.ndk_llvm_triple}{min_api}"
        flags.append(f"--target={target}")
        flags.append(f"--sysroot={self.toolchain.sysroot}")

        # Pour les applications non-console, lier les bibliothèques Android standards
        if project.kind != ProjectKind.CONSOLE_APP:
            flags.append("-llog")
            flags.append("-landroid")
            flags.append("-lEGL")
            flags.append("-lGLESv2")
        else:
            # Pour les exécutables, lier la bibliothèque C dynamique
            flags.append("-lc")
            flags.append("-ldl")

        # RPATH (pour les bibliothèques partagées)
        if project.kind != ProjectKind.CONSOLE_APP:
            flags.append("-Wl,-rpath-link=" + str(Path(self.toolchain.sysroot) / "usr" / "lib" / self.ndk_triple))
        flags.append("-Wl,--gc-sections")
        flags.append("-Wl,--no-undefined")

        # Flags supplémentaires
        if hasattr(project, 'ldflags'):
            flags.extend(project.ldflags)

        return flags

    def _OptionEnabled(self, name: str) -> bool:
        token = str(name or "").strip().lower()
        return any(str(opt).strip().lower() == token for opt in getattr(self, "options", []))

    def _GetOptionValue(self, name: str) -> Optional[str]:
        prefix = str(name or "").strip().lower() + "="
        for opt in getattr(self, "options", []):
            text = str(opt).strip().lower()
            if text.startswith(prefix):
                return text[len(prefix):]
        return None

    def _ShouldUseNdkMk(self) -> bool:
        mode = (self._GetOptionValue("android-build-system") or "").strip().lower()
        if mode in ("ndk-mk", "ndk-build", "mk"):
            return True
        if mode in ("native", "clang", "jenga-native"):
            return False
        return (
            self._OptionEnabled("android-mk")
            or self._OptionEnabled("use-android-mk")
            or self._OptionEnabled("android-build-system=ndk-mk")
        )

    def _ResolveNdkBuildPath(self) -> Optional[Path]:
        names = ["ndk-build.cmd", "ndk-build"] if sys.platform == "win32" else ["ndk-build", "ndk-build.cmd"]
        for name in names:
            candidate = self.ndk_path / name
            if candidate.exists():
                return candidate
        which = Process.Which("ndk-build")
        if which:
            return Path(which)
        return None

    def _FindProjectAndroidMk(self, project: Project) -> Tuple[Optional[Path], Optional[Path]]:
        project_root = Path(self.ResolveProjectPath(project, ".")).resolve()
        workspace_root = Path(self.workspace.location).resolve() if self.workspace and self.workspace.location else project_root

        android_candidates = [
            project_root / "Android.mk",
            project_root / "jni" / "Android.mk",
            workspace_root / "Android.mk",
            workspace_root / "jni" / "Android.mk",
        ]
        app_candidates = [
            project_root / "Application.mk",
            project_root / "jni" / "Application.mk",
            workspace_root / "Application.mk",
            workspace_root / "jni" / "Application.mk",
        ]

        android_mk = next((p for p in android_candidates if p.exists()), None)
        app_mk = next((p for p in app_candidates if p.exists()), None)
        return android_mk, app_mk

    def _CollectBuiltSharedLibs(self, libs_dir: Path) -> List[str]:
        abi_dir = libs_dir / self.ndk_abi
        if not abi_dir.exists():
            return []
        return [str(p) for p in sorted(abi_dir.glob("*.so")) if p.is_file()]

    def _BuildUsingNdkMk(self, targetProject: Optional[str] = None) -> int:
        ndk_build = self._ResolveNdkBuildPath()
        if not ndk_build:
            Reporter.Error("ndk-build not found. Install Android NDK and ensure ndk-build is available.")
            return 1

        app_projects: List[Project] = []
        for name, proj in self.workspace.projects.items():
            if name.startswith("__"):
                continue
            if targetProject and name != targetProject:
                continue
            if proj.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP):
                app_projects.append(proj)

        # If no app project is targeted, fallback to standard pipeline.
        if not app_projects:
            return super().Build(targetProject)

        for proj in app_projects:
            android_mk, app_mk = self._FindProjectAndroidMk(proj)
            if not android_mk:
                Reporter.Error(
                    f"Android.mk not found for project '{proj.name}'. "
                    "Generate it with `jenga gen --android-mk` or add one in the project/workspace."
                )
                return 1

            mk_build_dir = Path(self.GetTargetDir(proj)) / f"android-ndk-mk-{self.ndk_abi}"
            libs_out = mk_build_dir / "libs"
            obj_out = mk_build_dir / "obj"
            FileSystem.MakeDirectory(mk_build_dir)
            FileSystem.MakeDirectory(libs_out)
            FileSystem.MakeDirectory(obj_out)

            min_sdk = proj.androidMinSdk or self._GetMinApiLevel()
            ndk_debug = "1" if self.config.lower() == "debug" else "0"

            cmd = [
                str(ndk_build),
                f"NDK_PROJECT_PATH={mk_build_dir}",
                f"APP_BUILD_SCRIPT={android_mk}",
                f"NDK_LIBS_OUT={libs_out}",
                f"NDK_OUT={obj_out}",
                f"APP_ABI={self.ndk_abi}",
                f"APP_PLATFORM=android-{min_sdk}",
                f"NDK_DEBUG={ndk_debug}",
                f"-j{max(1, os.cpu_count() or 1)}",
            ]
            if app_mk:
                cmd.append(f"NDK_APPLICATION_MK={app_mk}")
            if self.verbose:
                cmd.append("V=1")

            Reporter.Info(f"Building with ndk-build ({proj.name})...")
            result = Process.ExecuteCommand(
                cmd,
                cwd=android_mk.parent,
                captureOutput=False,
                silent=False
            )
            if result.returnCode != 0:
                Reporter.Error(f"ndk-build failed for project '{proj.name}'")
                return 1

            native_libs = self._CollectBuiltSharedLibs(libs_out)
            if not native_libs:
                Reporter.Error(f"No shared libraries produced by ndk-build for '{proj.name}' ({self.ndk_abi})")
                return 1

            # Pour les projets console, on ne fait pas d'APK
            if proj.kind == ProjectKind.CONSOLE_APP:
                # Copier l'exécutable produit (ndk-build produit généralement un exécutable dans libs/<abi>/)
                exe_name = proj.targetName or proj.name
                exe_path = libs_out / self.ndk_abi / exe_name
                if exe_path.exists():
                    final_exe = Path(self.GetTargetDir(proj)) / exe_name
                    shutil.copy2(exe_path, final_exe)
                    Reporter.Success(f"Executable generated: {final_exe}")
                else:
                    Reporter.Error(f"Executable not found: {exe_path}")
                    return 1
            else:
                if not self.BuildAPK(proj, native_libs):
                    return 1

        return 0

    def Build(self, targetProject: Optional[str] = None) -> int:
        if self._ShouldUseNdkMk():
            return self._BuildUsingNdkMk(targetProject)

        code = super().Build(targetProject)
        if code != 0:
            return code

        app_projects: List[Project] = []
        for name, proj in self.workspace.projects.items():
            if targetProject and name != targetProject:
                continue
            if proj.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP):
                app_projects.append(proj)

        for proj in app_projects:
            # Pour les exécutables console, on ne fait pas d'APK
            if proj.kind == ProjectKind.CONSOLE_APP:
                exe_path = self.GetTargetPath(proj)
                if exe_path.exists():
                    Reporter.Success(f"Executable generated: {exe_path}")
                else:
                    Reporter.Error(f"Executable not built: {proj.name}")
                    return 1
                continue

            # Pour les applications graphiques, on collecte les bibliothèques natives
            native_libs: List[str] = []
            app_out = self.GetTargetPath(proj)
            if app_out.exists():
                native_libs.append(str(app_out))

            for dep_name in proj.dependsOn:
                dep = self.workspace.projects.get(dep_name)
                if not dep:
                    continue
                dep_out = self.GetTargetPath(dep)
                if dep.kind == ProjectKind.SHARED_LIB and dep_out.exists():
                    native_libs.append(str(dep_out))

            if not native_libs:
                Reporter.Error(f"No native outputs found for APK packaging: {proj.name}")
                return 1

            if self.build_aab:
                if not self.BuildAAB(proj, native_libs):
                    return 1
            else:
                if not self.BuildAPK(proj, native_libs):
                    return 1

        return 0

    # -----------------------------------------------------------------------
    # Packaging APK (modifié pour support Java complet)
    # -----------------------------------------------------------------------

    def BuildAPK(self, project: Project, nativeLibs: List[str]) -> bool:
        """
        Construit un APK signé et aligné.
        Gère les sources Java, les bibliothèques Java (.jar) et ProGuard/R8.
        """
        Reporter.Info(f"Building APK for {project.name} ({self.ndk_abi})")

        build_dir = Path(self.GetTargetDir(project)) / f"android-build-{self.ndk_abi}"
        FileSystem.RemoveDirectory(build_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(build_dir)

        # 1. Créer la structure de l'APK
        apk_unsigned_unaligned = build_dir / "app-unsigned-unaligned.apk"
        apk_unsigned_aligned = build_dir / "app-unsigned.apk"
        apk_signed = build_dir / f"{project.targetName or project.name}-{self.config}.apk"

        # 2. Compiler les ressources avec aapt2 (multi-dossiers)
        res_zip = build_dir / "resources.zip"
        if not self._CompileResources(project, build_dir, res_zip):
            return False

        # 3. Lier les ressources (génère R.java et resources.arsc)
        r_java_dir = build_dir / "gen"
        FileSystem.MakeDirectory(r_java_dir)
        if not self._LinkResources(project, res_zip, r_java_dir, build_dir):
            return False

        # 4. Collecter toutes les sources Java du projet (via androidJavaFiles)
        java_files = self._CollectJavaSourceFiles(project)
        java_libs = self._CollectJavaLibraries(project)

        # 5. Compiler le bytecode Java (sources + R.java) et les bibliothèques
        #    en classes .class, puis éventuellement passer par ProGuard
        classes_dir = build_dir / "classes"
        FileSystem.MakeDirectory(classes_dir)

        # Compiler les sources Java (si présentes) en .class
        if java_files or java_libs:
            if not self._CompileJava(project, r_java_dir, java_files, java_libs, classes_dir):
                return False

            # Appliquer ProGuard si demandé
            if project.androidProguard:
                if not self._RunProguard(project, classes_dir, java_libs, build_dir):
                    return False
                # Après ProGuard, les classes obfusquées sont dans un répertoire temporaire
                # On les utilise pour la suite
                proguard_out = build_dir / "proguard"
                classes_dir = proguard_out / "classes"  # à définir dans _RunProguard

        # 6. Convertir les .class et .jar en DEX avec d8
        dex_files = self._CompileDex(project, classes_dir, java_libs, build_dir)
        if dex_files is None:
            return False

        # 7. Assembler l'APK non signé
        if not self._AssembleApk(project, build_dir, dex_files, res_zip, nativeLibs, apk_unsigned_unaligned):
            return False

        # 8. Zipalign
        if not self._Zipalign(apk_unsigned_unaligned, apk_unsigned_aligned):
            return False

        # 9. Signer
        if project.androidSign:
            if not self._SignApk(project, apk_unsigned_aligned, apk_signed):
                return False
        else:
            shutil.copy2(apk_unsigned_aligned, apk_signed)

        # Also expose final APK in target dir for package/deploy commands.
        final_apk = Path(self.GetTargetDir(project)) / f"{project.targetName or project.name}.apk"
        shutil.copy2(apk_signed, final_apk)
        Reporter.Success(f"APK generated: {apk_signed}")
        return True

    def _CollectJavaSourceFiles(self, project: Project) -> List[Path]:
        """Collecte tous les fichiers .java via les patterns dans androidJavaFiles."""
        if not hasattr(project, 'androidJavaFiles'):
            return []
        patterns = project.androidJavaFiles
        proj_root = Path(self.ResolveProjectPath(project, "."))
        files = []
        for pattern in patterns:
            full_pattern = proj_root / pattern
            matches = glob.glob(str(full_pattern), recursive=True)
            for m in matches:
                p = Path(m)
                if p.is_file() and p.suffix == '.java':
                    files.append(p)
        return files

    def _CollectJavaLibraries(self, project: Project) -> List[Path]:
        """Collecte les fichiers .jar via androidJavaLibs."""
        if not hasattr(project, 'androidJavaLibs'):
            return []
        patterns = project.androidJavaLibs
        proj_root = Path(self.ResolveProjectPath(project, "."))
        libs = []
        for pattern in patterns:
            full_pattern = proj_root / pattern
            matches = glob.glob(str(full_pattern), recursive=True)
            for m in matches:
                p = Path(m)
                if p.is_file() and p.suffix == '.jar':
                    libs.append(p)
        return libs

    def _CompileJava(self, project: Project, r_java_dir: Path, java_files: List[Path],
                     java_libs: List[Path], classes_dir: Path) -> bool:
        """Compile les sources Java en .class avec javac."""
        # Résoudre javac
        javac_name = "javac.exe" if sys.platform == "win32" else "javac"
        javac = self.jdk_path / "bin" / javac_name
        if not javac.exists():
            javac_which = Process.Which("javac")
            if javac_which:
                javac = Path(javac_which)
            else:
                Colored.PrintError("javac not found")
                return False

        # Classpath: android.jar + toutes les bibliothèques Java
        classpath = [str(self.platform_jar)] + [str(lib) for lib in java_libs]
        cp_str = os.pathsep.join(classpath)

        # Ajouter R.java
        r_files = list(r_java_dir.rglob("*.java"))
        all_java = r_files + java_files

        if not all_java:
            # Aucune source Java
            return True

        # Compiler
        javac_cmd = [
            str(javac), "-d", str(classes_dir),
            "-classpath", cp_str,
            "-source", "1.8", "-target", "1.8"  # Compatibilité Android
        ] + [str(f) for f in all_java]

        result = Process.ExecuteCommand(javac_cmd, captureOutput=False, silent=False)
        return result.returnCode == 0

    def _FindProguardJar(self) -> Optional[Path]:
        """Recherche proguard.jar dans le SDK."""
        candidates = [
            self.sdk_path / "tools" / "proguard" / "lib" / "proguard.jar",
            self.sdk_path / "tools" / "proguard" / "proguard.jar",
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        return None

    def _RunProguard(self, project: Project, classes_dir: Path, java_libs: List[Path], build_dir: Path) -> bool:
        """Exécute ProGuard sur les classes compilées et les bibliothèques."""
        if not self.proguard_jar:
            Colored.PrintError("ProGuard jar not found in SDK. Please install ProGuard or disable proguard.")
            return False

        # Créer un répertoire de sortie pour ProGuard
        proguard_out = build_dir / "proguard"
        FileSystem.MakeDirectory(proguard_out)

        # Fichier de configuration ProGuard
        config_file = proguard_out / "proguard.cfg"
        with open(config_file, 'w') as f:
            # Règles de base
            f.write("-dontusemixedcaseclassnames\n")
            f.write("-dontskipnonpubliclibraryclasses\n")
            f.write("-verbose\n")
            f.write(f"-injars '{classes_dir}'\n")
            f.write(f"-outjars '{proguard_out / 'obfuscated.jar'}'\n")
            f.write(f"-libraryjars '{self.platform_jar}'\n")
            for lib in java_libs:
                f.write(f"-libraryjars '{lib}'\n")
            # Ajouter les règles utilisateur
            for rule in getattr(project, 'androidProguardRules', []):
                f.write(rule + "\n")
            # Règle par défaut pour garder les activités
            f.write("-keep public class * extends android.app.Activity\n")
            f.write("-keep public class * extends android.app.NativeActivity\n")
            f.write("-keep public class * extends android.app.Application\n")
            f.write("-keep public class * extends android.app.Service\n")
            f.write("-keep public class * extends android.content.BroadcastReceiver\n")
            f.write("-keep public class * extends android.content.ContentProvider\n")
            f.write("-keep public class * extends android.view.View {\n")
            f.write("    public <init>(android.content.Context);\n")
            f.write("    public <init>(android.content.Context, android.util.AttributeSet);\n")
            f.write("    public <init>(android.content.Context, android.util.AttributeSet, int);\n")
            f.write("}\n")

        # Exécuter ProGuard
        java = self.jdk_path / "bin" / "java"
        if not java.exists():
            java = Process.Which("java")
            if not java:
                Colored.PrintError("java not found")
                return False
        cmd = [
            str(java), "-jar", str(self.proguard_jar),
            f"@{config_file}"
        ]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        if result.returnCode != 0:
            return False

        # Extraire les classes obfusquées du jar
        obf_jar = proguard_out / "obfuscated.jar"
        if not obf_jar.exists():
            Colored.PrintError("ProGuard did not produce output jar")
            return False

        # Décompresser le jar dans proguard_out/classes
        obf_classes = proguard_out / "classes"
        FileSystem.MakeDirectory(obf_classes)
        with zipfile.ZipFile(obf_jar, 'r') as zf:
            zf.extractall(obf_classes)

        # Remplacer classes_dir par obf_classes pour la suite
        # On va renommer ou déplacer
        shutil.rmtree(classes_dir)
        shutil.copytree(obf_classes, classes_dir)
        return True

    def _CompileDex(self, project: Project, classes_dir: Path, java_libs: List[Path], build_dir: Path) -> Optional[List[Path]]:
        """
        Convertit les .class et .jar en DEX avec d8.
        Retourne la liste des fichiers .dex générés.
        """
        dex_out = build_dir / "dex"
        FileSystem.MakeDirectory(dex_out)

        # Collecter tous les .class dans classes_dir
        class_files = list(classes_dir.rglob("*.class"))
        if not class_files and not java_libs:
            # Pas de bytecode Java
            return []

        # Construire la commande d8
        d8_cmd = [str(self.d8), "--lib", str(self.platform_jar), "--output", str(dex_out)]
        # Ajouter les .jar
        for lib in java_libs:
            d8_cmd.append(str(lib))
        # Ajouter le répertoire de classes
        if class_files:
            d8_cmd.append(str(classes_dir))

        result = Process.ExecuteCommand(d8_cmd, captureOutput=False, silent=False)
        if result.returnCode != 0:
            return None

        # d8 produit un ou plusieurs .dex dans dex_out
        dex_files = list(dex_out.glob("*.dex"))
        return dex_files

    def _CompileResources(self, project: Project, build_dir: Path, output_zip: Path) -> bool:
        """aapt2 compile avec support de dossiers de ressources multiples."""
        proj_root = Path(self.ResolveProjectPath(project, "."))
        # Dossiers de ressources standards ou personnalisés
        res_dirs = []
        if hasattr(project, 'androidResDirs') and project.androidResDirs:
            for d in project.androidResDirs:
                p = Path(self.ResolveProjectPath(project, d))
                if p.exists():
                    res_dirs.append(p)
        else:
            # Par défaut, chercher res/ à la racine
            default_res = proj_root / "res"
            if default_res.exists():
                res_dirs.append(default_res)

        if not res_dirs:
            # Pas de ressources, créer un zip vide
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED):
                pass
            return True

        cmd = [str(self.aapt2), "compile"]
        for res in res_dirs:
            cmd += ["--dir", str(res)]
        cmd += ["-o", str(output_zip)]

        result = Process.ExecuteCommand(cmd, cwd=build_dir, captureOutput=False, silent=False)
        return result.returnCode == 0

    def _LinkResources(self, project: Project, res_zip: Path, r_java_dir: Path, build_dir: Path) -> bool:
        """aapt2 link."""
        manifest = Path(self.ResolveProjectPath(project, "AndroidManifest.xml"))
        if not manifest.exists():
            manifest = self._GenerateManifest(project, build_dir)

        cmd = [
            str(self.aapt2), "link",
            "-I", str(self.platform_jar),
            "--manifest", str(manifest),
            "--java", str(r_java_dir),
            "-o", str(build_dir / "resources.apk")
        ]
        if res_zip.exists() and res_zip.stat().st_size > 0:
            cmd.append(str(res_zip))

        result = Process.ExecuteCommand(cmd, cwd=build_dir, captureOutput=False, silent=False)
        return result.returnCode == 0

    def _GenerateManifest(self, project: Project, output_dir: Path) -> Path:
        """Crée un AndroidManifest.xml minimal (inchangé mais ajout de permissions)."""
        manifest_path = output_dir / "AndroidManifest.xml"
        android_ns = "http://schemas.android.com/apk/res/android"
        ET.register_namespace("android", android_ns)
        manifest = ET.Element(
            "manifest",
            {"package": project.androidApplicationId or f"com.{project.name}.app"}
        )
        manifest.set(f"{{{android_ns}}}versionCode", str(project.androidVersionCode or 1))
        manifest.set(f"{{{android_ns}}}versionName", project.androidVersionName or "1.0")

        uses_sdk = ET.SubElement(manifest, "uses-sdk")
        uses_sdk.set(f"{{{android_ns}}}minSdkVersion", str(project.androidMinSdk or 21))
        uses_sdk.set(f"{{{android_ns}}}targetSdkVersion", str(project.androidTargetSdk or 33))

        application = ET.SubElement(manifest, "application")
        application.set(f"{{{android_ns}}}label", project.name)
        # Détection de la présence de code Java
        has_java = bool(self._CollectJavaSourceFiles(project))
        application.set(f"{{{android_ns}}}hasCode", "true" if has_java else "false")

        if project.androidNativeActivity and not has_java:
            # NativeActivity sans code Java
            activity = ET.SubElement(application, "activity")
            activity.set(f"{{{android_ns}}}name", "android.app.NativeActivity")
            activity.set(f"{{{android_ns}}}exported", "true")
            meta = ET.SubElement(activity, "meta-data")
            meta.set(f"{{{android_ns}}}name", "android.app.lib_name")
            lib_basename = project.targetName or project.name
            if lib_basename.startswith("lib"):
                lib_basename = lib_basename[3:]
            meta.set(f"{{{android_ns}}}value", lib_basename)
            intent_filter = ET.SubElement(activity, "intent-filter")
            action = ET.SubElement(intent_filter, "action")
            action.set(f"{{{android_ns}}}name", "android.intent.action.MAIN")
            category = ET.SubElement(intent_filter, "category")
            category.set(f"{{{android_ns}}}name", "android.intent.category.LAUNCHER")
        elif has_java:
            # Si présence de code Java, on suppose que l'utilisateur a sa propre activité
            # On peut ajouter une activité par défaut si aucune n'est déclarée ?
            # Pour l'instant, on ne fait rien, l'utilisateur doit fournir son manifeste.
            pass

        # Ajouter les permissions
        for perm in getattr(project, 'androidPermissions', []):
            ET.SubElement(manifest, "uses-permission", {f"{{{android_ns}}}name": perm})

        tree = ET.ElementTree(manifest)
        tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
        return manifest_path

    def _AssembleApk(self, project: Project, build_dir: Path, dex_files: List[Path],
                     res_zip: Path, nativeLibs: List[str], apk_out: Path) -> bool:
        """Assemble l'APK non signé."""
        with zipfile.ZipFile(apk_out, 'w', zipfile.ZIP_DEFLATED) as zf:
            # DEX (classes.dex, classes2.dex, ...)
            for i, dex in enumerate(sorted(dex_files)):
                arcname = "classes.dex" if i == 0 else f"classes{i+1}.dex"
                zf.write(dex, arcname)

            # Ressources compilées (resources.arsc etc.)
            resources_apk = build_dir / "resources.apk"
            if resources_apk.exists():
                with zipfile.ZipFile(resources_apk, 'r') as res_apk:
                    for item in res_apk.infolist():
                        # Ne pas écraser les fichiers déjà présents
                        if item.filename not in zf.namelist():
                            zf.writestr(item, res_apk.read(item.filename))

            # Librairies natives
            for lib in nativeLibs:
                arcname = f"lib/{self.ndk_abi}/{Path(lib).name}"
                zf.write(lib, arcname)

            # AndroidManifest.xml
            manifest = build_dir / "AndroidManifest.xml"
            if manifest.exists():
                zf.write(manifest, "AndroidManifest.xml")

            # Assets (multi-dossiers)
            if hasattr(project, 'androidAssets'):
                for asset in project.androidAssets:
                    asset_path = Path(self.ResolveProjectPath(project, asset))
                    if asset_path.is_dir():
                        for f in asset_path.rglob("*"):
                            if f.is_file():
                                arcname = f"assets/{f.relative_to(asset_path)}"
                                zf.write(f, arcname)
                    else:
                        zf.write(asset_path, f"assets/{asset_path.name}")

        return True

    def _Zipalign(self, input_apk: Path, output_apk: Path) -> bool:
        """Aligne l'APK sur 4 octets."""
        cmd = [str(self.zipalign), "-f", "-p", "4", str(input_apk), str(output_apk)]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return result.returnCode == 0

    def _SignApk(self, project: Project, input_apk: Path, output_apk: Path) -> bool:
        """Signe l'APK avec apksigner."""
        if not project.androidKeystore:
            Colored.PrintError("Keystore not specified for signing")
            return False

        ks_pass = project.androidKeystorePass or ""
        key_alias = project.androidKeyAlias or project.name

        cmd = [
            str(self.apksigner), "sign",
            "--ks", project.androidKeystore,
            "--ks-pass", f"pass:{ks_pass}",
            "--ks-key-alias", key_alias,
            "--out", str(output_apk),
            str(input_apk)
        ]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return result.returnCode == 0

    # -----------------------------------------------------------------------
    # Packaging AAB (Android App Bundle) - version complète (inchangée)
    # -----------------------------------------------------------------------

    def BuildAAB(self, project: Project, nativeLibs: List[str]) -> bool:
        """
        Construit un Android App Bundle (AAB) signé.
        Nécessite bundletool et une structure de module.
        """
        Reporter.Info(f"Building AAB for {project.name} ({self.ndk_abi})")

        # Vérifier que bundletool est disponible
        bundletool = self._FindBundletool()
        if not bundletool:
            Colored.PrintError("bundletool not found. Please install via SDK Manager.")
            return False

        build_dir = Path(self.GetTargetDir(project)) / f"android-build-{self.ndk_abi}"
        aab_unsigned = build_dir / f"{project.targetName or project.name}-unsigned.aab"
        aab_signed = build_dir / f"{project.targetName or project.name}.aab"

        # Créer la structure de module
        module_dir = build_dir / "module"
        FileSystem.MakeDirectory(module_dir)

        # Copier les ressources, manifeste, dex, etc. dans la structure attendue par bundletool
        if not self._PrepareModule(project, module_dir, nativeLibs, build_dir):
            return False

        # Générer le bundle
        cmd = [
            str(bundletool), "build-bundle",
            "--modules", str(module_dir),
            "--output", str(aab_unsigned),
        ]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        if result.returnCode != 0:
            return False

        # Signer le bundle (optionnel)
        if project.androidSign:
            if not self._SignAAB(project, aab_unsigned, aab_signed):
                return False
        else:
            shutil.copy2(aab_unsigned, aab_signed)

        final_aab = Path(self.GetTargetDir(project)) / f"{project.targetName or project.name}.aab"
        shutil.copy2(aab_signed, final_aab)
        Reporter.Success(f"AAB generated: {aab_signed}")
        return True

    def _FindBundletool(self) -> Optional[Path]:
        """Recherche bundletool dans le SDK ou PATH."""
        bundletool = Process.Which("bundletool")
        if bundletool:
            return Path(bundletool)
        # Chemins typiques dans le SDK
        candidates = [
            self.sdk_path / "cmdline-tools" / "latest" / "bin" / "bundletool",
            self.sdk_path / "tools" / "bin" / "bundletool",
            self.sdk_path / "bundletool.jar",  # peut être un jar exécutable
        ]
        for cand in candidates:
            if cand.exists():
                return cand
        # Chercher bundletool.jar dans le dossier build-tools
        bt_jar = self.build_tools / "lib" / "bundletool.jar"
        if bt_jar.exists():
            return bt_jar
        return None

    def _PrepareModule(self, project: Project, module_dir: Path, nativeLibs: List[str], build_dir: Path) -> bool:
        """
        Prépare le contenu du module pour bundletool.
        Structure attendue :
          module/
            manifest/
              AndroidManifest.xml
            dex/
              ... (fichiers .dex)
            res/
              ... (ressources)
            lib/
              <abi>/
                ... (fichiers .so)
            assets/
              ... (assets)
            root/
              ... (fichiers supplémentaires)
        """
        # Manifeste
        manifest_src = build_dir / "AndroidManifest.xml"
        if not manifest_src.exists():
            manifest_src = self._GenerateManifest(project, build_dir)
        manifest_dir = module_dir / "manifest"
        FileSystem.MakeDirectory(manifest_dir)
        shutil.copy2(manifest_src, manifest_dir / "AndroidManifest.xml")

        # DEX
        dex_dir = module_dir / "dex"
        FileSystem.MakeDirectory(dex_dir)
        dex_files = list(build_dir.glob("dex/*.dex"))
        for dex in dex_files:
            shutil.copy2(dex, dex_dir / dex.name)

        # Ressources (resources.apk contient resources.arsc et les fichiers res/)
        resources_apk = build_dir / "resources.apk"
        if resources_apk.exists():
            with zipfile.ZipFile(resources_apk, 'r') as res_apk:
                res_dir = module_dir / "res"
                FileSystem.MakeDirectory(res_dir)
                for item in res_apk.infolist():
                    if item.filename.startswith("res/"):
                        target = res_dir / item.filename[4:]
                        FileSystem.MakeDirectory(target.parent)
                        with open(target, 'wb') as f:
                            f.write(res_apk.read(item.filename))
                    elif item.filename == "resources.arsc":
                        target = module_dir / "root" / "resources.arsc"
                        FileSystem.MakeDirectory(target.parent)
                        with open(target, 'wb') as f:
                            f.write(res_apk.read(item.filename))

        # Librairies natives
        lib_dir = module_dir / "lib" / self.ndk_abi
        FileSystem.MakeDirectory(lib_dir)
        for lib in nativeLibs:
            shutil.copy2(lib, lib_dir / Path(lib).name)

        # Assets
        if hasattr(project, 'androidAssets'):
            assets_dir = module_dir / "assets"
            FileSystem.MakeDirectory(assets_dir)
            for asset in project.androidAssets:
                asset_path = Path(self.ResolveProjectPath(project, asset))
                if asset_path.is_dir():
                    for f in asset_path.rglob("*"):
                        if f.is_file():
                            rel = f.relative_to(asset_path)
                            target = assets_dir / rel
                            FileSystem.MakeDirectory(target.parent)
                            shutil.copy2(f, target)
                else:
                    shutil.copy2(asset_path, assets_dir / asset_path.name)

        return True

    def _SignAAB(self, project: Project, input_aab: Path, output_aab: Path) -> bool:
        """Signe un AAB avec apksigner (même outil que pour APK)."""
        if not project.androidKeystore:
            Colored.PrintError("Keystore not specified for signing")
            return False

        ks_pass = project.androidKeystorePass or ""
        key_alias = project.androidKeyAlias or project.name

        cmd = [
            str(self.apksigner), "sign",
            "--ks", project.androidKeystore,
            "--ks-pass", f"pass:{ks_pass}",
            "--ks-key-alias", key_alias,
            "--out", str(output_aab),
            str(input_aab)
        ]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return result.returnCode == 0