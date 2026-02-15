#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Toolchains – Détection automatique et gestion des toolchains.
Fournit des méthodes pour :
  - Détecter les compilateurs installés (MSVC, GCC, Clang, Android NDK, Emscripten, MinGW)
  - Créer des objets Toolchain correspondants
  - Résoudre la toolchain à utiliser pour une cible donnée
"""

import os
import sys
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from Jenga.Core.Api import Toolchain, CompilerFamily, TargetOS, TargetArch, TargetEnv
from ..Utils import Process, FileSystem
from .Platform import Platform
from .GlobalToolchains import GetJengaRoot


class ToolchainManager:
    """
    Gestionnaire global de toolchains.
    Peut être instancié pour un workspace ou utilisé statiquement.
    """

    def __init__(self, workspace: Optional[Any] = None):
        self.workspace = workspace
        self._detected: Dict[str, Toolchain] = {}
        self._cache: Dict[Tuple[TargetOS, TargetArch, Optional[TargetEnv]], Optional[str]] = {}

    def _GetCompilersRoot(self, workspace: Optional[Any] = None) -> Optional[Path]:
        wks = workspace or self.workspace
        if wks and getattr(wks, "location", ""):
            root = Path(wks.location).resolve() / ".jenga" / "compilers"
            if root.exists():
                return root
        global_root = GetJengaRoot() / ".jenga" / "compilers"
        return global_root if global_root.exists() else None

    def _CollectExtraBinaryPaths(self, workspace: Optional[Any] = None) -> List[str]:
        root = self._GetCompilersRoot(workspace)
        if not root:
            return []
        paths: List[str] = []
        candidates = [root, root / "bin"]
        for child in root.iterdir():
            if child.is_dir():
                candidates.append(child)
                candidates.append(child / "bin")
        for p in candidates:
            if p.exists() and p.is_dir():
                paths.append(str(p))
        # De-duplicate while preserving order.
        deduped: List[str] = []
        seen = set()
        for p in paths:
            if p in seen:
                continue
            seen.add(p)
            deduped.append(p)
        return deduped

    # -----------------------------------------------------------------------
    # Détection des compilateurs hôtes – priorité : Clang > GCC > MSVC
    # -----------------------------------------------------------------------

    @staticmethod
    def DetectHostCC() -> Optional[Toolchain]:
        """Détecte le compilateur C par défaut sur le système."""
        def _first_runnable(candidates: List[str]) -> Optional[str]:
            for name in candidates:
                p = Process.Which(name)
                if not p:
                    continue
                try:
                    probe = Process.ExecuteCommand([p, "--version"], captureOutput=True, silent=True)
                    if probe.returnCode == 0:
                        return p
                except Exception:
                    continue
            return None

        cc_path = _first_runnable(["clang", "gcc", "cc", "zig-cc"])
        if not cc_path:
            return None

        cxx_path = _first_runnable(["clang++", "g++", "c++", "zig-c++"]) or cc_path
        ar_path = Process.Which("llvm-ar") or Process.Which("ar")
        ld_path = Process.Which("ld") or cc_path

        family = ToolchainManager._DetectCompilerFamily(cc_path)
        name = f"host-{family.value}"
        tc = Toolchain(
            name=name,
            compilerFamily=family,
            ccPath=cc_path,
            cxxPath=cxx_path,
            arPath=ar_path,
            ldPath=ld_path,
        )
        tc.targetOs = Platform.GetHostOS()
        tc.targetArch = Platform.GetHostArchitecture()

        if sys.platform == 'win32':
            if family == CompilerFamily.GCC:
                tc.targetEnv = TargetEnv.MINGW
            elif family == CompilerFamily.CLANG:
                cc_low = (cc_path or "").lower()
                # MSYS2/UCRT/MinGW clang should default to MinGW ABI.
                if any(token in cc_low for token in ("msys64", "mingw", "ucrt")):
                    tc.targetEnv = TargetEnv.MINGW
                elif not Process.Which("clang-cl"):
                    tc.targetEnv = TargetEnv.MINGW
                else:
                    tc.targetEnv = TargetEnv.MSVC
            else:
                tc.targetEnv = Platform.GetHostEnvironment()
        else:
            tc.targetEnv = Platform.GetHostEnvironment()
        return tc

    @staticmethod
    def DetectMSVC() -> Optional[Toolchain]:
        """Détecte Visual Studio / MSVC (Windows uniquement). Retourne une toolchain incomplète."""
        if sys.platform != "win32":
            return None
        vswhere_path = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) \
                       / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
        if vswhere_path.exists():
            try:
                result = Process.Capture([str(vswhere_path), "-latest", "-property", "installationPath"])
                install_path = Path(result.strip())
                vcvars = install_path / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
                if vcvars.exists():
                    tc = Toolchain(
                        name="msvc",
                        compilerFamily=CompilerFamily.MSVC,
                        toolchainDir=str(vcvars.parent),
                    )
                    tc.targetOs = TargetOS.WINDOWS
                    tc.targetArch = Platform.GetHostArchitecture()
                    tc.targetEnv = TargetEnv.MSVC
                    return tc
            except:
                pass
        editions = ["Community", "Professional", "Enterprise", "BuildTools"]
        years = ["2022", "2019", "2017"]
        base = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Microsoft Visual Studio"
        for year in years:
            for edition in editions:
                vcvars = base / year / edition / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
                if vcvars.exists():
                    tc = Toolchain(
                        name="msvc",
                        compilerFamily=CompilerFamily.MSVC,
                        toolchainDir=str(vcvars.parent),
                    )
                    tc.targetOs = TargetOS.WINDOWS
                    tc.targetArch = Platform.GetHostArchitecture()
                    tc.targetEnv = TargetEnv.MSVC
                    return tc
        return None

    @staticmethod
    def DetectClangOnWindows() -> Optional[Toolchain]:
        """Détecte Clang sur Windows. clang-cl -> MSVC ABI, clang -> MinGW ABI."""
        if sys.platform != "win32":
            return None
        # Prefer clang/clang++ MinGW-style toolchain (MSYS2/UCRT) when present.
        clang_path = Process.Which("clang")
        clangpp_path = Process.Which("clang++")
        if clang_path and clangpp_path:
            tc = Toolchain(
                name="clang-mingw",
                compilerFamily=CompilerFamily.CLANG,
                ccPath=clang_path,
                cxxPath=clangpp_path,
                arPath=Process.Which("llvm-ar") or Process.Which("ar"),
                ldPath=clangpp_path,
            )
            tc.targetOs = TargetOS.WINDOWS
            tc.targetArch = Platform.GetHostArchitecture()
            tc.targetEnv = TargetEnv.MINGW
            return tc

        clang_cl_path = Process.Which("clang-cl")
        if clang_cl_path:
            tc = Toolchain(
                name="clang-cl",
                compilerFamily=CompilerFamily.CLANG,
                ccPath=clang_cl_path,
                cxxPath=clang_cl_path,
                arPath=Process.Which("llvm-ar") or Process.Which("ar"),
                ldPath=Process.Which("lld-link") or clang_cl_path,
            )
            tc.targetOs = TargetOS.WINDOWS
            tc.targetArch = Platform.GetHostArchitecture()
            tc.targetEnv = TargetEnv.MSVC
            return tc
        return None

    @staticmethod
    def DetectMinGW() -> Optional[Toolchain]:
        """Détecte MinGW-w64 (gcc/g++ sous Windows)."""
        if sys.platform != "win32":
            return None
        gcc_path = Process.Which("x86_64-w64-mingw32-gcc") or Process.Which("gcc")
        if not gcc_path:
            return None
        gpp_path = Process.Which("x86_64-w64-mingw32-g++") or Process.Which("g++")
        ar_path = Process.Which("x86_64-w64-mingw32-ar") or Process.Which("ar")
        tc = Toolchain(
            name="mingw",
            compilerFamily=CompilerFamily.GCC,
            ccPath=gcc_path,
            cxxPath=gpp_path or gcc_path,
            arPath=ar_path,
            ldPath=Process.Which("ld") or gcc_path,
        )
        tc.targetOs = TargetOS.WINDOWS
        tc.targetArch = Platform.GetHostArchitecture()
        tc.targetEnv = TargetEnv.MINGW
        return tc

    @staticmethod
    def _DetectCompilerFamily(compiler_path: str) -> CompilerFamily:
        """Détermine la famille du compilateur à partir de --version."""
        try:
            out = Process.Capture([compiler_path, "--version"])
            out_lower = out.lower()
            if "clang" in out_lower:
                if "apple" in out_lower:
                    return CompilerFamily.APPLE_CLANG
                return CompilerFamily.CLANG
            if "zig" in out_lower:
                return CompilerFamily.CLANG
            if "gcc" in out_lower or "g++" in out_lower:
                return CompilerFamily.GCC
            if "msvc" in out_lower or "microsoft" in out_lower:
                return CompilerFamily.MSVC
            if "emscripten" in out_lower:
                return CompilerFamily.EMSCRIPTEN
        except:
            pass
        return CompilerFamily.GCC

    @staticmethod
    def DetectAndroidNDK(ndkPath: Optional[Path] = None) -> Optional[Toolchain]:
        """Détecte le NDK Android et crée une toolchain générique."""
        if ndkPath is None:
            candidates = []
            if "ANDROID_NDK_ROOT" in os.environ:
                candidates.append(Path(os.environ["ANDROID_NDK_ROOT"]))
            if "ANDROID_NDK_HOME" in os.environ:
                candidates.append(Path(os.environ["ANDROID_NDK_HOME"]))
            if "ANDROID_HOME" in os.environ:
                candidates.append(Path(os.environ["ANDROID_HOME"]) / "ndk-bundle")
            if sys.platform == "win32":
                candidates.append(Path("C:/Program Files/Android/NDK"))
            elif sys.platform == "darwin":
                candidates.append(Path("~/Library/Android/sdk/ndk-bundle").expanduser())
            else:
                candidates.append(Path("~/Android/Sdk/ndk-bundle").expanduser())
            if "JENGA_COMPILERS_DIR" in os.environ:
                root = Path(os.environ["JENGA_COMPILERS_DIR"])
                candidates.append(root / "android" / "ndk")
                sdk_ndk = root / "android" / "sdk" / "ndk"
                if sdk_ndk.exists():
                    for version in sorted(sdk_ndk.iterdir(), reverse=True):
                        candidates.append(version)
            for cand in candidates:
                if cand and cand.exists():
                    ndkPath = cand
                    break
        if not ndkPath or not ndkPath.exists():
            return None
        llvm_dir = None
        for p in ndkPath.glob("toolchains/llvm/prebuilt/*"):
            if p.is_dir():
                llvm_dir = p
                break
        if not llvm_dir:
            return None
        tc = Toolchain(
            name="android-ndk",
            compilerFamily=CompilerFamily.ANDROID_NDK,
            toolchainDir=str(llvm_dir),
            ccPath=str(llvm_dir / "bin" / "clang"),
            cxxPath=str(llvm_dir / "bin" / "clang++"),
            arPath=str(llvm_dir / "bin" / "llvm-ar"),
            ldPath=str(llvm_dir / "bin" / "ld"),
            stripPath=str(llvm_dir / "bin" / "llvm-strip"),
            ranlibPath=str(llvm_dir / "bin" / "llvm-ranlib"),
        )
        tc.targetOs = TargetOS.ANDROID
        tc.targetArch = TargetArch.ARM64
        tc.targetEnv = TargetEnv.ANDROID
        return tc

    @staticmethod
    def DetectEmscripten(emsdkPath: Optional[Path] = None) -> Optional[Toolchain]:
        """Détecte Emscripten SDK."""
        emcc_from_path = Process.Which("emcc")
        emcc_direct = Path(emcc_from_path) if emcc_from_path else None
        if emsdkPath is None:
            if emcc_direct:
                # Typical layouts:
                # - <emsdk>/upstream/emscripten/emcc(.bat)
                # - <emsdk>/emcc(.bat)
                parent = emcc_direct.parent
                if parent.name.lower() == "emscripten" and parent.parent.name.lower() == "upstream":
                    emsdkPath = parent.parent.parent
                else:
                    emsdkPath = parent.parent
            else:
                if sys.platform == "win32":
                    candidates = [Path("C:/emsdk")]
                else:
                    candidates = [Path.home() / "emsdk", Path("/opt/emsdk")]
                if "JENGA_COMPILERS_DIR" in os.environ:
                    candidates.append(Path(os.environ["JENGA_COMPILERS_DIR"]) / "emsdk")
                for cand in candidates:
                    if cand.exists():
                        emsdkPath = cand
                        break
        if not emsdkPath or not emsdkPath.exists():
            return None
        emcc_candidates = []
        if emcc_direct and emcc_direct.exists():
            emcc_candidates.append(emcc_direct)
        names = ["emcc", "emcc.bat", "emcc.cmd", "emcc.exe"]
        for name in names:
            emcc_candidates.extend([
                emsdkPath / name,
                emsdkPath / "emsdk" / name,
                emsdkPath / "upstream" / "emscripten" / name,
            ])
        emcc_path = None
        for cand in emcc_candidates:
            if cand.exists():
                emcc_path = cand
                break
        if not emcc_path:
            return None
        em_dir = emcc_path.parent
        empp_path = None
        emar_path = None
        for name in ("em++", "em++.bat", "em++.cmd", "em++.exe"):
            cand = em_dir / name
            if cand.exists():
                empp_path = cand
                break
        for name in ("emar", "emar.bat", "emar.cmd", "emar.exe"):
            cand = em_dir / name
            if cand.exists():
                emar_path = cand
                break
        tc = Toolchain(
            name="emscripten",
            compilerFamily=CompilerFamily.EMSCRIPTEN,
            toolchainDir=str(emsdkPath),
            ccPath=str(emcc_path),
            cxxPath=str(empp_path or (em_dir / "em++")),
            arPath=str(emar_path or (em_dir / "emar")),
        )
        tc.targetOs = TargetOS.WEB
        tc.targetArch = TargetArch.WASM32
        return tc

    @staticmethod
    def DetectCrossLinuxOnWindows() -> Optional[Toolchain]:
        """Détecte un cross-compilateur Linux sur Windows (GNU or clang --target)."""
        if sys.platform != "win32":
            return None

        # Prefer a real GNU cross toolchain if available.
        gcc_candidates = [
            ("x86_64-linux-gnu-gcc", "x86_64-linux-gnu-g++", "x86_64-linux-gnu-ar", "x86_64-unknown-linux-gnu"),
            ("x86_64-pc-linux-gnu-gcc", "x86_64-pc-linux-gnu-g++", "x86_64-pc-linux-gnu-ar", "x86_64-pc-linux-gnu"),
        ]
        for cc_name, cxx_name, ar_name, triple in gcc_candidates:
            gcc_path = Process.Which(cc_name)
            if not gcc_path:
                continue
            tc = Toolchain(
                name="gcc-cross-linux",
                compilerFamily=CompilerFamily.GCC,
                ccPath=gcc_path,
                cxxPath=Process.Which(cxx_name) or gcc_path,
                arPath=Process.Which(ar_name) or Process.Which("ar"),
                ldPath=Process.Which(cxx_name) or gcc_path,
            )
            tc.targetOs = TargetOS.LINUX
            tc.targetArch = TargetArch.X86_64
            tc.targetEnv = TargetEnv.GNU
            tc.targetTriple = triple
            return tc

        # Fallback: clang with Linux target triple (compile support check).
        clang_path = Process.Which("clang")
        clangxx_path = Process.Which("clang++")
        if clang_path and clangxx_path:
            triple = "x86_64-unknown-linux-gnu"
            test_cmd = [clang_path, f"--target={triple}", "-c", "-x", "c", "-", "-o", os.devnull]
            try:
                result = Process.ExecuteCommand(test_cmd, captureOutput=True, input="int main(){return 0;}\n", silent=True)
                if result.returnCode == 0:
                    tc = Toolchain(
                        name="clang-cross-linux",
                        compilerFamily=CompilerFamily.CLANG,
                        ccPath=clang_path,
                        cxxPath=clangxx_path,
                        arPath=Process.Which("llvm-ar") or Process.Which("ar"),
                        ldPath=clangxx_path,
                    )
                    tc.targetOs = TargetOS.LINUX
                    tc.targetArch = TargetArch.X86_64
                    tc.targetEnv = TargetEnv.GNU
                    tc.targetTriple = triple
                    tc.cflags.append(f"--target={triple}")
                    tc.cxxflags.append(f"--target={triple}")
                    tc.ldflags.append(f"--target={triple}")
                    return tc
            except Exception:
                pass
        return None

    # -----------------------------------------------------------------------
    # Interface publique
    # -----------------------------------------------------------------------

    def DetectAll(self, workspace: Optional[Any] = None) -> Dict[str, Toolchain]:
        """Détecte toutes les toolchains disponibles et les retourne. Ordre de priorité : Clang, GCC, autres."""
        toolchains = {}
        original_path = os.environ.get("PATH", "")
        old_compilers_env = os.environ.get("JENGA_COMPILERS_DIR")
        compilers_root = self._GetCompilersRoot(workspace)
        extra_paths = self._CollectExtraBinaryPaths(workspace)
        try:
            if extra_paths:
                os.environ["PATH"] = os.pathsep.join(extra_paths + [original_path])
            if compilers_root:
                os.environ["JENGA_COMPILERS_DIR"] = str(compilers_root)

            # 1. Clang hôte
            host_cc = self.DetectHostCC()
            if host_cc and host_cc.compilerFamily == CompilerFamily.CLANG:
                toolchains[host_cc.name] = host_cc
            # 2. Clang sur Windows (MinGW)
            if sys.platform == "win32":
                clang_win = self.DetectClangOnWindows()
                if clang_win:
                    toolchains[clang_win.name] = clang_win
            # 3. GCC hôte
            host_gcc = self.DetectHostCC()
            if host_gcc and host_gcc.compilerFamily == CompilerFamily.GCC and host_gcc.name not in toolchains:
                toolchains[host_gcc.name] = host_gcc
            # 4. MinGW (gcc)
            if sys.platform == "win32":
                mingw = self.DetectMinGW()
                if mingw and mingw.name not in toolchains:
                    toolchains[mingw.name] = mingw
            # 5. Cross Linux on Windows
            if sys.platform == "win32":
                cross_linux = self.DetectCrossLinuxOnWindows()
                if cross_linux and cross_linux.name not in toolchains:
                    toolchains[cross_linux.name] = cross_linux
            # 6. Android NDK
            android = self.DetectAndroidNDK()
            if android:
                toolchains[android.name] = android
            # 7. Emscripten
            emscripten = self.DetectEmscripten()
            if emscripten:
                toolchains[emscripten.name] = emscripten
            # MSVC n'est pas ajouté automatiquement (incomplet)
            self._detected = toolchains
            return toolchains
        finally:
            os.environ["PATH"] = original_path
            if old_compilers_env is None:
                os.environ.pop("JENGA_COMPILERS_DIR", None)
            else:
                os.environ["JENGA_COMPILERS_DIR"] = old_compilers_env

    def ResolveForTarget(self,
                         targetOs: TargetOS,
                         targetArch: TargetArch,
                         targetEnv: Optional[TargetEnv] = None,
                         prefer: Optional[List[str]] = None) -> Optional[str]:
        """Trouve la meilleure toolchain pour une cible donnée."""
        cache_key = (targetOs, targetArch, targetEnv)
        if cache_key in self._cache:
            return self._cache[cache_key]
        candidates = []
        for name, tc in self._detected.items():
            if tc.targetOs == targetOs and tc.targetArch == targetArch:
                if targetEnv is None or tc.targetEnv == targetEnv:
                    candidates.append(name)
        if not candidates:
            for name, tc in self._detected.items():
                if tc.targetOs == targetOs:
                    candidates.append(name)
        if not candidates:
            self._cache[cache_key] = None
            return None
        if prefer:
            for pref in prefer:
                if pref in candidates:
                    self._cache[cache_key] = pref
                    return pref
        selected = candidates[0]
        self._cache[cache_key] = selected
        return selected

    def GetToolchain(self, name: str) -> Optional[Toolchain]:
        return self._detected.get(name)

    def AddToolchain(self, toolchain: Toolchain) -> None:
        self._detected[toolchain.name] = toolchain

    def ClearCache(self) -> None:
        self._cache.clear()
