#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android Builder – Compilation pour Android via NDK.
Gère les bibliothèques natives (.so), packaging APK/AAB, signature.
Support complet : armeabi-v7a, arm64-v8a, x86, x86_64.
"""

import os
import shutil
import xml.etree.ElementTree as ET
import zipfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import tempfile, sys

from Jenga.Core.Api import Project, ProjectKind, TargetArch, TargetOS
from ...Utils import Process, FileSystem, Colored, Reporter
from ..Builder import Builder
from ..Toolchains import ToolchainManager


class AndroidBuilder(Builder):
    """
    Builder pour Android.
    Supporte :
      - Compilation NDK (C/C++)
      - Packaging APK signé (debug/release)
      - Packaging AAB (Android App Bundle)
      - ProGuard / R8
      - Assets et ressources
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)

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
        self.d8 = self._ToolPath("d8")  # ou dx.jar selon version

        self.platform_jar = self.sdk_path / "platforms" / f"android-{self._GetTargetSdkVersion()}" / "android.jar"
        if not self.platform_jar.exists():
            # Fallback: version la plus haute disponible
            platforms = sorted([p for p in (self.sdk_path / "platforms").glob("android-*")], reverse=True)
            if platforms:
                self.platform_jar = platforms[0] / "android.jar"

        # Configurer la toolchain NDK pour l'architecture cible
        self._PrepareNDKToolchain()

    # -----------------------------------------------------------------------
    # Résolution des chemins SDK/NDK/JDK
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
    # Configuration NDK
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
    # Compilation native
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
        else:
            return ".so"  # les exécutables Android sont des .so avec NativeActivity

    def GetTargetPath(self, project: Project) -> Path:
        target_dir = self.GetTargetDir(project)
        target_name = project.targetName or project.name
        ext = self.GetOutputExtension(project)
        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.SHARED_LIB):
            if not target_name.startswith("lib"):
                target_name = f"lib{target_name}"
        elif project.kind == ProjectKind.STATIC_LIB:
            if not target_name.startswith("lib"):
                target_name = f"lib{target_name}"
        return target_dir / f"{target_name}{ext}"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [compiler, "-c", "-o", str(obj)]
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
            args = [linker, "-shared", "-o", str(out)]
            args.extend(self._GetLinkerFlags(project))
            # Object files first; archives are order-sensitive.
            final_objects = list(objectFiles)
            if project.androidNativeActivity:
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
        if project.androidNativeActivity:
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

        # PIC
        flags.append("-fPIC")

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

        # Librairies standards Android
        flags.append("-llog")
        flags.append("-landroid")
        flags.append("-lEGL")
        flags.append("-lGLESv2")

        # RPATH
        flags.append("-Wl,-rpath-link=" + str(Path(self.toolchain.sysroot) / "usr" / "lib" / self.ndk_triple))
        flags.append("-Wl,--gc-sections")
        flags.append("-Wl,--no-undefined")

        # Flags supplémentaires
        if hasattr(project, 'ldflags'):
            flags.extend(project.ldflags)

        return flags

    def Build(self, targetProject: Optional[str] = None) -> int:
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

            if not self.BuildAPK(proj, native_libs):
                return 1

        return 0

    # -----------------------------------------------------------------------
    # Packaging APK
    # -----------------------------------------------------------------------

    def BuildAPK(self, project: Project, nativeLibs: List[str]) -> bool:
        """
        Construit un APK signé et aligné.
        """
        Reporter.Info(f"Building APK for {project.name} ({self.ndk_abi})")

        build_dir = Path(self.GetTargetDir(project)) / f"android-build-{self.ndk_abi}"
        FileSystem.RemoveDirectory(build_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(build_dir)

        # 1. Créer la structure de l'APK
        apk_unsigned_unaligned = build_dir / "app-unsigned-unaligned.apk"
        apk_unsigned_aligned = build_dir / "app-unsigned.apk"
        apk_signed = build_dir / f"{project.targetName or project.name}-{self.config}.apk"

        # 2. Compiler les ressources avec aapt2
        res_zip = build_dir / "resources.zip"
        if not self._CompileResources(project, build_dir, res_zip):
            return False

        # 3. Lier les ressources (génère R.java et resources.arsc)
        r_java_dir = build_dir / "gen"
        FileSystem.MakeDirectory(r_java_dir)
        if not self._LinkResources(project, res_zip, r_java_dir, build_dir):
            return False

        # 4. Compiler le bytecode Java (R.java, etc.) et les éventuels .java du projet
        dex_file = build_dir / "classes.dex"
        if not self._CompileDex(project, r_java_dir, dex_file):
            return False

        # 5. Assembler l'APK non signé
        if not self._AssembleApk(project, build_dir, dex_file, res_zip, nativeLibs, apk_unsigned_unaligned):
            return False

        # 6. Zipalign
        if not self._Zipalign(apk_unsigned_unaligned, apk_unsigned_aligned):
            return False

        # 7. Signer
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

    def _CompileResources(self, project: Project, build_dir: Path, output_zip: Path) -> bool:
        """aapt2 compile."""
        proj_root = Path(self.ResolveProjectPath(project, "."))
        res_dirs = [proj_root / "res"]

        existing_res = [res for res in res_dirs if res.exists()]
        if not existing_res:
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED):
                pass
            return True

        cmd = [str(self.aapt2), "compile"]
        for res in existing_res:
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
        """Crée un AndroidManifest.xml minimal."""
        manifest_path = output_dir / "AndroidManifest.xml"
        android_ns = "http://schemas.android.com/apk/res/android"
        ET.register_namespace("android", android_ns)
        manifest = ET.Element(
            "manifest",
            {"package": project.androidApplicationId or f"com.{project.name}.app"}
        )
        manifest.set(f"{{{android_ns}}}versionCode", str(project.androidVersionCode))
        manifest.set(f"{{{android_ns}}}versionName", project.androidVersionName or "1.0")

        uses_sdk = ET.SubElement(manifest, "uses-sdk")
        uses_sdk.set(f"{{{android_ns}}}minSdkVersion", str(project.androidMinSdk))
        uses_sdk.set(f"{{{android_ns}}}targetSdkVersion", str(project.androidTargetSdk))

        application = ET.SubElement(manifest, "application")
        application.set(f"{{{android_ns}}}label", project.name)
        application.set(f"{{{android_ns}}}hasCode", "false" if project.androidNativeActivity else "true")

        if project.androidNativeActivity:
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

        # Ajouter les permissions
        for perm in project.androidPermissions:
            ET.SubElement(manifest, "uses-permission", {f"{{{android_ns}}}name": perm})

        tree = ET.ElementTree(manifest)
        tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
        return manifest_path

    def _CompileDex(self, project: Project, r_java_dir: Path, dex_out: Path) -> bool:
        """Compile le bytecode Java en Dalvik Executable (DEX)."""
        # Compiler R.java avec javac
        java_files = list(r_java_dir.rglob("*.java"))
        if not java_files:
            # NativeActivity app without Java bytecode.
            return True
        else:
            classes_dir = r_java_dir.parent / "classes"
            FileSystem.MakeDirectory(classes_dir)

            # Résoudre javac avec extension sur Windows
            javac_name = "javac.exe" if sys.platform == "win32" else "javac"
            javac = self.jdk_path / "bin" / javac_name

            # Fallback: chercher dans PATH si non trouvé
            if not javac.exists():
                javac_which = Process.Which("javac")
                if javac_which:
                    javac = Path(javac_which)

            javac_cmd = [
                str(javac), "-d", str(classes_dir),
                "-classpath", str(self.platform_jar)
            ] + [str(f) for f in java_files]

            result = Process.ExecuteCommand(javac_cmd, captureOutput=False, silent=False)
            if result.returnCode != 0:
                return False

            cmd = [str(self.d8), "--lib", str(self.platform_jar), "--output", str(dex_out.parent)]
            cmd += list(classes_dir.rglob("*.class"))

        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return result.returnCode == 0

    def _AssembleApk(self, project: Project, build_dir: Path, dex_file: Path,
                     res_zip: Path, nativeLibs: List[str], apk_out: Path) -> bool:
        """Assemble l'APK non signé."""
        with zipfile.ZipFile(apk_out, 'w', zipfile.ZIP_DEFLATED) as zf:
            # DEX
            if dex_file.exists():
                zf.write(dex_file, "classes.dex")

            # Ressources compilées
            resources_apk = build_dir / "resources.apk"
            if resources_apk.exists():
                with zipfile.ZipFile(resources_apk, 'r') as res_apk:
                    for item in res_apk.infolist():
                        zf.writestr(item, res_apk.read(item.filename))

            # Librairies natives
            for lib in nativeLibs:
                arcname = f"lib/{self.ndk_abi}/{Path(lib).name}"
                zf.write(lib, arcname)

            # AndroidManifest.xml
            manifest = build_dir / "AndroidManifest.xml"
            if manifest.exists():
                zf.write(manifest, "AndroidManifest.xml")

            # Assets
            if project.androidAssets:
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
    # Packaging AAB (Android App Bundle)
    # -----------------------------------------------------------------------

    def BuildAAB(self, project: Project, nativeLibs: List[str]) -> bool:
        """
        Construit un Android App Bundle (AAB) signé.
        Nécessite bundletool.
        """
        Reporter.Info(f"Building AAB for {project.name} ({self.ndk_abi})")

        # Vérifier que bundletool est disponible
        bundletool = Process.Which("bundletool")
        if not bundletool:
            # Chercher dans le SDK
            bundletool = self.sdk_path / "cmdline-tools" / "latest" / "bin" / "bundletool"
            if not bundletool.exists():
                bundletool = self.sdk_path / "tools" / "bin" / "bundletool"
        if not bundletool or not Path(bundletool).exists():
            Colored.PrintError("bundletool not found. Please install via SDK Manager.")
            return False

        build_dir = Path(self.GetTargetDir(project)) / f"android-build-{self.ndk_abi}"
        aab_path = build_dir / f"{project.targetName or project.name}.aab"

        # Créer le bundle
        cmd = [
            str(bundletool), "build-bundle",
            "--modules", str(build_dir / "modules"),
            "--output", str(aab_path),
            "--config", str(self._GenerateBundleConfig(project, build_dir))
        ]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        return result.returnCode == 0

    def _GenerateBundleConfig(self, project: Project, build_dir: Path) -> Path:
        """Génère un fichier de configuration pour bundletool."""
        config = {
            "optimizations": {
                "splitsConfig": {
                    "splitDimension": [
                        {"value": "ABI", "negate": False},
                        {"value": "SCREEN_DENSITY", "negate": False},
                        {"value": "LANGUAGE", "negate": False}
                    ]
                }
            },
            "compression": {"uncompressedGlob": ["res/raw/**", "assets/**"]}
        }
        import json
        config_path = build_dir / "BundleConfig.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return config_path
