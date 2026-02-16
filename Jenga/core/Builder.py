#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Builder – Classe de base pour tous les builders de plateforme.
Coordonne le build : résolution des dépendances, compilation, link.
"""

import abc
import time
import glob
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

from Jenga.Core import Api
from Jenga.Core.Api import Workspace, Project, Toolchain, ProjectKind, TargetOS, TargetArch, TargetEnv, CompilerFamily
from ..Utils import FileSystem, Process, Colored, Reporter, BuildLogger
from .State import BuildState
from .DependencyResolver import DependencyResolver
from .Toolchains import ToolchainManager
from .Platform import Platform


class Builder(abc.ABC):
    """
    Classe abstraite de base pour un builder spécifique à une plateforme/cible.
    Chaque sous-classe doit implémenter :
      - Compile()
      - Link()
      - GetOutputExtension()
    """

    def __init__(self,
                 workspace: Workspace,
                 config: str,
                 platform: str,
                 targetOs: TargetOS,
                 targetArch: TargetArch,
                 targetEnv: Optional[TargetEnv] = None,
                 verbose: bool = False):
        self.workspace = workspace
        self.config = config
        self.platform = platform
        self.targetOs = targetOs
        self.targetArch = targetArch
        # Keep target env optional: when unspecified, toolchain resolution can
        # pick the best available ABI/environment for the target OS.
        self.targetEnv = targetEnv
        self.verbose = verbose

        self._expander = None
        if workspace:
            from .Variables import VariableExpander
            self._expander = VariableExpander(workspace=workspace)
            platform_value = platform if platform else targetOs.value
            target_env_value = targetEnv.value if targetEnv else ""
            self._expander.SetConfig({
                'name': config,
                'buildcfg': config,
                'configuration': config,
                'platform': platform_value,
                'system': targetOs.value,
                'os': targetOs.value,
                'arch': targetArch.value,
                'architecture': targetArch.value,
                'targetos': targetOs.value,
                'targetarch': targetArch.value,
                'env': target_env_value,
                'targetenv': target_env_value,
            })

        self.state = BuildState(workspace)
        self.toolchainManager = ToolchainManager(workspace)
        self.toolchain: Optional[Toolchain] = None
        self._lastResult = None  # Last ProcessResult from compile/link

        self._ValidateHostTarget()
        self._ResolveToolchain()

    def _ValidateHostTarget(self):
        host_os = Platform.GetHostOS()
        if self.targetOs == TargetOS.MACOS and host_os != TargetOS.MACOS:
            raise RuntimeError(f"Cannot build for macOS from {host_os.value}. macOS builds require macOS with Apple toolchain.")
        if self.targetOs == TargetOS.IOS and host_os != TargetOS.MACOS:
            raise RuntimeError(f"Cannot build for iOS from {host_os.value}. iOS builds require macOS with Xcode.")
        if self.targetOs in (TargetOS.XBOX_ONE, TargetOS.XBOX_SERIES) and host_os != TargetOS.WINDOWS:
            raise RuntimeError(f"Cannot build for Xbox from {host_os.value}. Xbox builds require Windows with Microsoft GDK.")
        if self.targetOs == TargetOS.TVOS and host_os != TargetOS.MACOS:
            raise RuntimeError("tvOS builds require macOS.")
        if self.targetOs == TargetOS.WATCHOS and host_os != TargetOS.MACOS:
            raise RuntimeError("watchOS builds require macOS.")

    def _ResolveToolchain(self) -> None:
        if self.workspace.defaultToolchain:
            tc_name = self.workspace.defaultToolchain
            tc = self.workspace.toolchains.get(tc_name)
            if tc:
                self.toolchain = tc
                return
        self.toolchainManager.DetectAll(self.workspace)
        prefer = []
        if self.targetOs == TargetOS.WINDOWS:
            prefer = ['clang-mingw', 'mingw', 'clang-cl', 'host-clang', 'host-gcc']
        elif self.targetOs == TargetOS.LINUX:
            prefer = ['host-clang', 'host-gcc', 'clang-cross-linux', 'gcc-cross-linux']
        elif self.targetOs == TargetOS.MACOS:
            prefer = ['host-apple-clang']
        elif self.targetOs == TargetOS.ANDROID:
            prefer = ['android-ndk']
        elif self.targetOs == TargetOS.IOS:
            prefer = ['host-apple-clang']
        elif self.targetOs == TargetOS.WEB:
            prefer = ['emscripten']
        tc_name = self.toolchainManager.ResolveForTarget(self.targetOs, self.targetArch, self.targetEnv, prefer=prefer)
        if tc_name:
            self.toolchain = self.toolchainManager.GetToolchain(tc_name)
        if not self.toolchain:
            raise RuntimeError(f"No suitable toolchain found for {self.targetOs.value} {self.targetArch.value}")

    # -----------------------------------------------------------------------
    # Méthodes abstraites
    # -----------------------------------------------------------------------

    @abc.abstractmethod
    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        pass

    @abc.abstractmethod
    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        pass

    @abc.abstractmethod
    def GetOutputExtension(self, project: Project) -> str:
        pass

    @abc.abstractmethod
    def GetObjectExtension(self) -> str:
        pass

    @abc.abstractmethod
    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        """Retourne les flags de compilation pour un fichier module C++20."""
        pass

    def PreparePCH(self, project: Project, objDir: Path) -> bool:
        """
        Optional PCH preparation hook.
        Builders may set:
          - project._jengaPchFile
          - project._jengaPchHeaderResolved
          - project._jengaPchSourceResolved
        """
        return True

    # -----------------------------------------------------------------------
    # Méthodes communes
    # -----------------------------------------------------------------------

    def GetObjectDir(self, project: Project) -> Path:
        if project.objDir:
            if self._expander:
                self._expander.SetProject(project)
                expanded = self._expander.Expand(project.objDir, recursive=True)
                return Path(expanded).resolve()
            else:
                return Path(project.objDir).resolve()
        else:
            base = Path(self.workspace.location) / "Build" / "Obj" / self.config
            if self.platform:
                base = base / self.platform
            return (base / project.name).resolve()

    def GetTargetDir(self, project: Project) -> Path:
        if project.targetDir:
            if self._expander:
                self._expander.SetProject(project)
                expanded = self._expander.Expand(project.targetDir, recursive=True)
                return Path(expanded).resolve()
            else:
                return Path(project.targetDir).resolve()
        else:
            base = Path(self.workspace.location) / "Build"
            if project.kind in (ProjectKind.STATIC_LIB, ProjectKind.SHARED_LIB):
                base = base / "Lib"
            else:
                base = base / "Bin"
            base = base / self.config
            if self.platform:
                base = base / self.platform
            return (base / project.name).resolve()

    def GetTargetPath(self, project: Project) -> Path:
        target_dir = self.GetTargetDir(project)
        target_name = project.targetName or project.name
        ext = self.GetOutputExtension(project)
        return target_dir / f"{target_name}{ext}"

    def ResolveProjectPath(self, project: Project, value: str) -> str:
        """Resolve a project-relative path against project.location."""
        if not value:
            return value
        if '%{' in value:
            return value
        p = Path(value)
        if p.is_absolute():
            return str(p)

        workspace_base = Path(self.workspace.location).resolve() if self.workspace and self.workspace.location else Path.cwd()
        if project.location:
            base_dir_str = project.location
            if self._expander:
                self._expander.SetProject(project)
                base_dir_str = self._expander.Expand(base_dir_str, recursive=True)
            base_dir_path = Path(base_dir_str)
            if not base_dir_path.is_absolute():
                base_dir_path = workspace_base / base_dir_path
            base_dir = base_dir_path.resolve()
        else:
            base_dir = workspace_base
        return str((base_dir / p).resolve())

    # -----------------------------------------------------------------------
    # Filter application (system/config)
    # -----------------------------------------------------------------------

    @staticmethod
    def _NormalizeSystemName(system_name: str) -> str:
        raw = (system_name or "").strip().lower()
        aliases = {
            "win": "windows",
            "win32": "windows",
            "win64": "windows",
            "linux": "linux",
            "gnu/linux": "linux",
            "mac": "macos",
            "osx": "macos",
            "darwin": "macos",
            "web": "web",
            "emscripten": "web",
            "ios": "ios",
            "android": "android",
            "harmony": "harmonyos",
            "harmonyos": "harmonyos",
        }
        return aliases.get(raw, raw)

    def _FilterMatches(self, filter_name: str) -> bool:
        """Return True if a filter string matches current build context."""
        if not filter_name:
            return False
        raw = filter_name.strip()
        lowered = raw.lower()

        # system:Windows
        if lowered.startswith("system:"):
            system_value = raw.split(":", 1)[1].strip()
            expected = self._NormalizeSystemName(system_value)
            active_os = self._NormalizeSystemName(self.targetOs.value)
            active_platform = ""
            if self.platform:
                active_platform = self._NormalizeSystemName(self.platform.split("-", 1)[0])
            return expected in {active_os, active_platform}

        # configurations:Debug, configuration:Release, config:Debug
        for prefix in ("configurations:", "configuration:", "config:", "cfg:"):
            if lowered.startswith(prefix):
                cfg_value = raw.split(":", 1)[1].strip().lower()
                return cfg_value == self.config.lower()

        # architecture:x86_64 / arch:arm64
        for prefix in ("architecture:", "arch:", "targetarch:"):
            if lowered.startswith(prefix):
                arch_value = raw.split(":", 1)[1].strip().lower()
                return arch_value == self.targetArch.value.lower()

        # platform:Windows-x86_64
        if lowered.startswith("platform:"):
            platform_value = raw.split(":", 1)[1].strip().lower()
            active_platform = (self.platform or "").strip().lower()
            if active_platform:
                return platform_value == active_platform
            # fallback: compare against target os when --platform not explicitly set
            return platform_value == self.targetOs.value.lower()

        return False

    @staticmethod
    def _AppendUnique(items: List[str], values: List[str]) -> None:
        for value in values:
            if value not in items:
                items.append(value)

    def _ApplyProjectFilters(self, project: Project) -> None:
        """
        Materialize filtered properties onto project for the active target/config.
        Called once per project/build context.
        """
        context_key = f"{self.targetOs.value}|{self.targetArch.value}|{self.config}|{self.platform or ''}"
        if getattr(project, "_jenga_applied_filter_context", None) == context_key:
            return

        # Snapshot project base values once, then re-materialize on each context.
        base = getattr(project, "_jenga_filter_base_state", None)
        if base is None:
            base = {
                "files": list(project.files),
                "excludeFiles": list(project.excludeFiles),
                "excludeMainFiles": list(project.excludeMainFiles),
                "includeDirs": list(project.includeDirs),
                "libDirs": list(project.libDirs),
                "links": list(project.links),
                "defines": list(project.defines),
                "objDir": project.objDir,
                "targetDir": project.targetDir,
                "targetName": project.targetName,
                "pchHeader": project.pchHeader,
                "pchSource": project.pchSource,
                "optimize": project.optimize,
                "symbols": project.symbols,
                "warnings": project.warnings,
            }
            project._jenga_filter_base_state = base

        project.files = list(base["files"])
        project.excludeFiles = list(base["excludeFiles"])
        project.excludeMainFiles = list(base["excludeMainFiles"])
        project.includeDirs = list(base["includeDirs"])
        project.libDirs = list(base["libDirs"])
        project.links = list(base["links"])
        project.defines = list(base["defines"])
        project.objDir = base["objDir"]
        project.targetDir = base["targetDir"]
        project.targetName = base["targetName"]
        project.pchHeader = base["pchHeader"]
        project.pchSource = base["pchSource"]
        project.optimize = base["optimize"]
        project.symbols = base["symbols"]
        project.warnings = base["warnings"]

        # 1) system links collected via links() inside filter("system:...")
        active_system = self._NormalizeSystemName(self.targetOs.value)
        for system_name, libs in project.systemLinks.items():
            if self._NormalizeSystemName(system_name) == active_system:
                self._AppendUnique(project.links, list(libs))
        for system_name, defs in project.systemDefines.items():
            if self._NormalizeSystemName(system_name) == active_system:
                self._AppendUnique(project.defines, list(defs))

        # 2) generic filtered properties captured by API
        for filter_name, files in getattr(project, "_filteredFiles", {}).items():
            if self._FilterMatches(filter_name):
                self._AppendUnique(project.files, list(files))
        for filter_name, files in getattr(project, "_filteredExcludeFiles", {}).items():
            if self._FilterMatches(filter_name):
                self._AppendUnique(project.excludeFiles, list(files))
        for filter_name, files in getattr(project, "_filteredExcludeMainFiles", {}).items():
            if self._FilterMatches(filter_name):
                self._AppendUnique(project.excludeMainFiles, list(files))
        for filter_name, dirs in getattr(project, "_filteredIncludeDirs", {}).items():
            if self._FilterMatches(filter_name):
                self._AppendUnique(project.includeDirs, list(dirs))
        for filter_name, dirs in getattr(project, "_filteredLibDirs", {}).items():
            if self._FilterMatches(filter_name):
                self._AppendUnique(project.libDirs, list(dirs))

        for filter_name, defs in project._filteredDefines.items():
            if self._FilterMatches(filter_name):
                self._AppendUnique(project.defines, list(defs))
        for filter_name, links in getattr(project, "_filteredLinks", {}).items():
            if self._FilterMatches(filter_name):
                self._AppendUnique(project.links, list(links))
        for filter_name, obj_dir in getattr(project, "_filteredObjDir", {}).items():
            if self._FilterMatches(filter_name):
                project.objDir = obj_dir
        for filter_name, target_dir in getattr(project, "_filteredTargetDir", {}).items():
            if self._FilterMatches(filter_name):
                project.targetDir = target_dir
        for filter_name, target_name in getattr(project, "_filteredTargetName", {}).items():
            if self._FilterMatches(filter_name):
                project.targetName = target_name
        for filter_name, pch_header in getattr(project, "_filteredPchHeader", {}).items():
            if self._FilterMatches(filter_name):
                project.pchHeader = pch_header
        for filter_name, pch_source in getattr(project, "_filteredPchSource", {}).items():
            if self._FilterMatches(filter_name):
                project.pchSource = pch_source

        for filter_name, opt in project._filteredOptimize.items():
            if self._FilterMatches(filter_name):
                project.optimize = opt

        for filter_name, sym in project._filteredSymbols.items():
            if self._FilterMatches(filter_name):
                project.symbols = sym

        for filter_name, warn in project._filteredWarnings.items():
            if self._FilterMatches(filter_name):
                project.warnings = warn

        project._jenga_applied_filter_context = context_key

    # -----------------------------------------------------------------------
    # Incremental compilation helpers
    # -----------------------------------------------------------------------

    def GetDependencyFilePath(self, objectFile: str) -> Path:
        """Dependency sidecar path used by GCC/Clang style compilers."""
        return Path(f"{objectFile}.d")

    def GetDependencyFlags(self, objectFile: str) -> List[str]:
        """
        Dependency emission flags for GCC/Clang:
        -MMD (user headers), -MF (output), -MT (target).
        """
        dep_file = self.GetDependencyFilePath(objectFile)
        return ["-MMD", "-MF", str(dep_file), "-MT", str(objectFile)]

    def _ParseDependencyFile(self, depFile: Path, project: Project) -> List[Path]:
        """
        Parse a Make-style .d dependency file and return normalized paths.
        This parser is tolerant to Windows drive letters and escaped colons.
        """
        if not depFile.exists():
            return []
        try:
            content = depFile.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        content = content.replace("\\\r\n", " ").replace("\\\n", " ")
        tokens = content.split()
        deps: List[Path] = []
        after_target = False

        for token in tokens:
            if token == "\\":
                continue
            if not after_target:
                if token.endswith(":"):
                    after_target = True
                continue

            cleaned = token.strip().rstrip("\\")
            cleaned = cleaned.replace("\\ ", " ").replace("\\:", ":")
            if not cleaned:
                continue

            p = Path(cleaned)
            if not p.is_absolute():
                p = Path(self.ResolveProjectPath(project, cleaned))
            else:
                p = p.resolve()
            deps.append(p)

        return deps

    def _NeedsCompileSource(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        """
        Return True if source must be recompiled:
          - object missing
          - source newer than object
          - dependency file missing
          - any dependency newer than object
        """
        src = Path(sourceFile)
        obj = Path(objectFile)
        if not src.exists():
            return False
        if not obj.exists():
            return True

        obj_mtime = obj.stat().st_mtime
        if src.stat().st_mtime > obj_mtime:
            return True

        dep_file = self.GetDependencyFilePath(objectFile)
        if not dep_file.exists():
            return True

        deps = self._ParseDependencyFile(dep_file, project)
        if not deps:
            return True

        for dep in deps:
            try:
                if dep.exists() and dep.stat().st_mtime > obj_mtime:
                    return True
            except OSError:
                return True

        return False

    # ============================================================
    # Support modules C++20
    # ============================================================

    def _ExtractModuleName(self, moduleFile: str) -> str:
        """
        Extrait le nom du module depuis 'export module <name>;'

        Args:
            moduleFile: Chemin du fichier module (.cppm, .ixx, etc.)

        Returns:
            Nom du module ou nom du fichier sans extension si non trouvé
        """
        try:
            with open(moduleFile, 'r', encoding='utf-8') as f:
                for line in f:
                    # Chercher 'export module <name>;'
                    line_stripped = line.strip()
                    if line_stripped.startswith('export') and 'module' in line_stripped:
                        # export module math;
                        # export module utils.string;
                        parts = line_stripped.split()
                        if len(parts) >= 3 and parts[0] == 'export' and parts[1] == 'module':
                            module_name = parts[2].rstrip(';')
                            return module_name
        except Exception as e:
            Colored.PrintWarning(f"Could not extract module name from {moduleFile}: {e}")

        # Fallback : utiliser le nom du fichier
        return Path(moduleFile).stem

    def _GetBMIExtension(self) -> str:
        """Retourne l'extension BMI selon le compilateur."""
        if self.toolchain.compilerFamily == CompilerFamily.MSVC:
            return ".ifc"
        else:  # Clang/GCC
            return ".pcm"

    def _PrecompileModules(self, project: Project, module_files: List[str], obj_dir: Path) -> bool:
        """
        Précompile tous les modules C++20 pour générer les BMI.

        Args:
            project: Projet en cours
            module_files: Liste des fichiers modules
            obj_dir: Répertoire des fichiers objets

        Returns:
            True si succès, False sinon
        """
        bmi_dir = obj_dir / "modules"
        FileSystem.MakeDirectory(bmi_dir)

        for mod_file in module_files:
            src = Path(mod_file)
            mod_name = self._ExtractModuleName(str(src))
            bmi_ext = self._GetBMIExtension()
            bmi_path = bmi_dir / f"{src.stem}{bmi_ext}"

            # Commande de précompilation selon le compilateur
            if self.toolchain.compilerFamily == CompilerFamily.MSVC:
                # MSVC: cl /std:c++20 /interface module.cppm /Fo module.ifc
                args = [str(self.toolchain.cxxPath), "/std:c++20", "/interface",
                        str(src), "/Fo", str(bmi_path)]
                args.extend(self._GetModulePCHIncludes(project))
            elif self.toolchain.compilerFamily == CompilerFamily.GCC:
                # GCC: g++ -std=c++20 -fmodules-ts -c module.cppm -o module.o
                # Note: GCC génère directement un .o, pas de BMI séparé
                args = [str(self.toolchain.cxxPath), "-std=c++20", "-fmodules-ts",
                        "-c", str(src), "-o", str(bmi_path.with_suffix('.o'))]
                args.extend(self._GetCompilerFlagsForModules(project))
            else:  # Clang (défaut)
                # Clang: clang++ -std=c++20 --precompile module.cppm -o module.pcm
                args = [str(self.toolchain.cxxPath), "-std=c++20", "--precompile",
                        str(src), "-o", str(bmi_path)]
                args.extend(self._GetCompilerFlagsForModules(project))

            # Exécuter la précompilation
            result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
            self._lastResult = result
            if result.returnCode != 0:
                Colored.PrintError(f"Failed to precompile module: {mod_file}")
                return False

            # Stocker le BMI pour utilisation ultérieure
            project._jengaModuleBMIs[mod_name] = str(bmi_path)
            Reporter.Success(f"Module '{mod_name}' precompiled -> {bmi_path.name}")

        return True

    def _CompileModuleToObject(self, project: Project, moduleFile: str, objectFile: str, obj_dir: Path) -> bool:
        """
        Compile un BMI de module en fichier objet.

        Pour Clang/MSVC: compile le .pcm/.ifc en .o
        Pour GCC: le .o est déjà généré par _PrecompileModules

        Args:
            project: Projet en cours
            moduleFile: Fichier module source
            objectFile: Fichier objet destination
            obj_dir: Répertoire objets

        Returns:
            True si succès, False sinon
        """
        # GCC génère directement un .o, donc on copie juste
        if self.toolchain.compilerFamily == CompilerFamily.GCC:
            mod_name = self._ExtractModuleName(moduleFile)
            bmi_path = project._jengaModuleBMIs.get(mod_name)
            if bmi_path and Path(bmi_path).exists():
                # Le .o existe déjà depuis la précompilation
                import shutil
                shutil.copy2(bmi_path, objectFile)
                return True
            return False

        # Pour Clang/MSVC: compiler le BMI en objet
        mod_name = self._ExtractModuleName(moduleFile)
        bmi_path = project._jengaModuleBMIs.get(mod_name)

        if not bmi_path or not Path(bmi_path).exists():
            Colored.PrintError(f"BMI not found for module {mod_name}")
            return False

        if self.toolchain.compilerFamily == CompilerFamily.MSVC:
            # MSVC: cl /c /Fo output.o module.ifc
            args = [str(self.toolchain.cxxPath), "/c", "/Fo", objectFile, bmi_path]
        else:  # Clang
            # Clang: clang++ -c -o output.o module.pcm
            args = [str(self.toolchain.cxxPath), "-c", "-o", objectFile, bmi_path]
            args.extend(self._GetCompilerFlagsForModules(project))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def _GetCompilerFlagsForModules(self, project: Project) -> List[str]:
        """Retourne les flags de compilation pour les modules."""
        flags = []

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{self.ResolveProjectPath(project, inc)}")

        # Defines
        for define in project.defines:
            flags.append(f"-D{define}")

        # Debug
        if project.symbols:
            flags.append("-g")

        # Optimization
        opt = project.optimize.value if hasattr(project.optimize, 'value') else project.optimize
        if opt == "Off":
            flags.append("-O0")
        elif opt == "Size":
            flags.append("-Os")
        elif opt == "Speed":
            flags.append("-O2")
        elif opt == "Full":
            flags.append("-O3")

        return flags

    def _GetModulePCHIncludes(self, project: Project) -> List[str]:
        """Retourne les flags pour MSVC."""
        flags = []

        # Includes
        for inc in project.includeDirs:
            flags.append(f"/I{self.ResolveProjectPath(project, inc)}")

        # Defines
        for define in project.defines:
            flags.append(f"/D{define}")

        return flags

    def _GetModuleImportFlags(self, project: Project) -> List[str]:
        """
        Retourne les flags nécessaires pour importer les modules C++20 précompilés.

        Returns:
            Liste de flags à ajouter lors de la compilation
        """
        flags = []
        module_bmis = getattr(project, '_jengaModuleBMIs', {})

        if not module_bmis:
            return flags

        for mod_name, bmi_path in module_bmis.items():
            if self.toolchain.compilerFamily == CompilerFamily.MSVC:
                # MSVC: /reference:module_name=path/to/module.ifc
                flags.append(f"/reference:{mod_name}={bmi_path}")
            else:  # Clang/GCC
                # Clang: -fmodule-file=module_name=path/to/module.pcm
                flags.append(f"-fmodule-file={mod_name}={bmi_path}")

        return flags

    def BuildProject(self, project: Project) -> bool:
        if self.state.IsProjectCompiled(project.name):
            return True

        # Apply filter(system/config) materialization before any build decision.
        self._ApplyProjectFilters(project)

        # Create logger with project info
        kind_str = project.kind.name if hasattr(project.kind, 'name') else str(project.kind)
        workspace_root = self.workspace.location if self.workspace else None
        logger = BuildLogger(project.name, kind_str, workspace_root)

        # Print beautiful project header
        logger.PrintProjectHeader()

        obj_dir = self.GetObjectDir(project)
        FileSystem.MakeDirectory(obj_dir)
        sources = self._CollectSourceFiles(project)
        if not sources:
            Colored.PrintWarning(f"No source files found for project {project.name}")
            self.state.MarkProjectCompiled(project.name, success=True)
            return True
        if not self.PreparePCH(project, obj_dir):
            self.state.MarkProjectCompiled(project.name, success=False)
            return False
        pch_source = getattr(project, "_jengaPchSourceResolved", "")
        if pch_source:
            pch_src_norm = str(Path(pch_source).resolve())
            sources = [s for s in sources if str(Path(s).resolve()) != pch_src_norm]

        # ===== Support modules C++20 =====
        module_files = [s for s in sources if self.IsModuleFile(s)]
        regular_files = [s for s in sources if not self.IsModuleFile(s)]

        project._jengaModuleBMIs = {}

        # Set total for logger
        logger.SetTotal(len(module_files) + len(regular_files))

        # Precompile modules
        if module_files:
            Reporter.Info(f"Precompiling {len(module_files)} C++20 module(s)...")
            if not self._PrecompileModules(project, module_files, obj_dir):
                self.state.MarkProjectCompiled(project.name, success=False)
                logger.PrintResultBox(False)
                return False

        object_files = []
        success = True

        # Compile modules to object files
        for mod_file in module_files:
            src_path = Path(mod_file)
            obj_name = src_path.with_suffix(self.GetObjectExtension()).name
            obj_path = obj_dir / obj_name

            self._lastResult = None
            if self._CompileModuleToObject(project, str(src_path), str(obj_path), obj_dir):
                object_files.append(str(obj_path))
                self.state.AddProjectOutput(project.name, str(obj_path))
                logger.LogCompile(str(src_path), self._lastResult)
            else:
                logger.LogCompile(str(src_path), self._lastResult)
                success = False
                break

        if not success:
            self.state.MarkProjectCompiled(project.name, success=False)
            logger.PrintStats()
            return False

        # Compile regular sources
        for src in regular_files:
            src_path = Path(src)
            obj_name = src_path.with_suffix(self.GetObjectExtension()).name
            obj_path = obj_dir / obj_name

            if not self._NeedsCompileSource(project, str(src_path), str(obj_path)):
                object_files.append(str(obj_path))
                self.state.AddProjectOutput(project.name, str(obj_path))
                logger.LogCached(str(src_path))
                continue

            self._lastResult = None
            if self.Compile(project, str(src_path), str(obj_path)):
                object_files.append(str(obj_path))
                self.state.AddProjectOutput(project.name, str(obj_path))
                logger.LogCompile(str(src_path), self._lastResult)
            else:
                logger.LogCompile(str(src_path), self._lastResult)
                success = False
                break
        if not success:
            self.state.MarkProjectCompiled(project.name, success=False)
            logger.PrintStats()
            return False

        # Auto-wire local library dependencies for link phase while preserving
        # the user-declared link order (important for GNU-like linkers).
        dep_link_map: Dict[str, str] = {}
        for dep_name in project.dependsOn:
            dep_proj = self.workspace.projects.get(dep_name)
            if not dep_proj:
                continue
            if dep_proj.kind not in (ProjectKind.STATIC_LIB, ProjectKind.SHARED_LIB):
                continue
            dep_dir = str(self.GetTargetDir(dep_proj))
            dep_out = str(self.GetTargetPath(dep_proj))
            if dep_dir not in project.libDirs:
                project.libDirs.append(dep_dir)
            dep_link_map[dep_name] = dep_out

        if dep_link_map:
            new_links: List[str] = []
            seen: set[str] = set()

            for link in project.links:
                resolved = dep_link_map.get(link, link)
                if resolved not in seen:
                    new_links.append(resolved)
                    seen.add(resolved)

            # Ensure dependencies are present even if not explicitly listed in links().
            missing_dep_outputs: List[str] = []
            for dep_out in dep_link_map.values():
                if dep_out not in seen:
                    missing_dep_outputs.append(dep_out)
                    seen.add(dep_out)

            # Missing auto-wired dependency archives are prepended so that
            # GNU-like linkers resolve their symbols before system/provider libs.
            project.links = missing_dep_outputs + new_links

        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP,
                            ProjectKind.SHARED_LIB, ProjectKind.STATIC_LIB,
                            ProjectKind.TEST_SUITE):
            target_path = self.GetTargetPath(project)
            FileSystem.MakeDirectory(target_path.parent)

            self._lastResult = None
            if self.Link(project, object_files, str(target_path)):
                self.state.AddProjectOutput(project.name, str(target_path))
                self.state.MarkProjectCompiled(project.name, success=True)
                logger.LogLink(str(target_path), self._lastResult)
                logger.PrintResultBox(True)
                return True
            else:
                logger.LogLink(str(target_path), self._lastResult)
                self.state.MarkProjectCompiled(project.name, success=False)
                logger.PrintResultBox(False)
                return False
        else:
            self.state.MarkProjectCompiled(project.name, success=True)
            logger.PrintResultBox(True)
            return True

    @staticmethod
    def GetSourceFileExtensions(language: Api.Language) -> List[str]:
        extensions = {
            Api.Language.C:        ['.c'],
            Api.Language.CPP:      ['.cpp', '.cc', '.cxx', '.c++', '.cppm', '.ixx', '.mpp', '.c++m'],
            Api.Language.OBJC:     ['.m'],
            Api.Language.OBJCPP:   ['.mm'],
            Api.Language.ASM:      ['.s', '.asm', '.S'],
            Api.Language.RUST:     ['.rs'],
            Api.Language.ZIG:      ['.zig'],
        }
        return extensions.get(language, ['.c', '.cpp', '.cc', '.cxx', '.m', '.mm'])

    @staticmethod
    def IsModuleFile(filepath: str) -> bool:
        ext = Path(filepath).suffix.lower()
        return ext in ('.cppm', '.ixx', '.mpp', '.c++m')

    @staticmethod
    def GetHeaderFileExtensions() -> List[str]:
        return ['.h', '.hpp', '.hxx', '.h++', '.inl', '.inc', '.tpp', '.ipp']

    @staticmethod
    def GetObjectExtensionForPlatform(platform: str) -> str:
        if platform.lower() in ('windows', 'win32', 'win64', 'msvc'):
            return '.obj'
        else:
            return '.o'

    @staticmethod
    def GetOutputExtensionsForProject(project: Project) -> List[str]:
        exts = []
        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            exts.append('.exe')
            exts.append('')
        elif project.kind == ProjectKind.SHARED_LIB:
            exts.extend(['.dll', '.so', '.dylib'])
            exts.append('.lib')
        elif project.kind == ProjectKind.STATIC_LIB:
            exts.extend(['.lib', '.a'])
        return exts

    def _CollectSourceFiles(self, project: Project) -> List[str]:
        files = []
        workspace_base = Path(self.workspace.location).resolve() if self.workspace and self.workspace.location else Path.cwd()
        if project.location:
            base_dir_str = project.location
            if self._expander:
                self._expander.SetProject(project)
                base_dir_str = self._expander.Expand(base_dir_str, recursive=True)
            base_dir_path = Path(base_dir_str)
            if not base_dir_path.is_absolute():
                base_dir_path = workspace_base / base_dir_path
            base_dir = base_dir_path.resolve()
        else:
            base_dir = workspace_base
        src_exts = self.GetSourceFileExtensions(project.language)
        for pattern in project.files:
            expanded_pattern = pattern
            if self._expander:
                self._expander.SetProject(project)
                expanded_pattern = self._expander.Expand(pattern, recursive=True)
            p = Path(expanded_pattern)
            if p.is_absolute():
                if any(ch in expanded_pattern for ch in ("*", "?", "[")):
                    matched = [m for m in glob.glob(expanded_pattern, recursive=True) if Path(m).is_file()]
                elif p.exists():
                    matched = [str(p)]
                else:
                    matched = []
            else:
                matched = FileSystem.ListFiles(base_dir, pattern=expanded_pattern, recursive=True, fullPath=True)
            for f in matched:
                if any(f.lower().endswith(ext) for ext in src_exts):
                    files.append(f)
        exclude = set()
        for pattern in project.excludeFiles:
            expanded_pattern = pattern
            if self._expander:
                self._expander.SetProject(project)
                expanded_pattern = self._expander.Expand(pattern, recursive=True)
            p = Path(expanded_pattern)
            if p.is_absolute():
                if any(ch in expanded_pattern for ch in ("*", "?", "[")):
                    matched = [m for m in glob.glob(expanded_pattern, recursive=True) if Path(m).is_file()]
                elif p.exists():
                    matched = [str(p)]
                else:
                    matched = []
            else:
                matched = FileSystem.ListFiles(base_dir, pattern=expanded_pattern, recursive=True, fullPath=True)
            exclude.update(matched)
        files = [f for f in files if f not in exclude]
        files.sort()
        return files

    def Build(self, targetProject: Optional[str] = None) -> int:
        from ..Utils.Reporter import BuildCoordinator

        # Resolve build order
        try:
            order = DependencyResolver.ResolveBuildOrder(self.workspace, targetProject)
        except RuntimeError as e:
            Reporter.Error(f"Dependency resolution failed: {e}")
            return 1

        # Prepare build order information for header
        build_order_info = []
        for proj_name in order:
            proj = self.workspace.projects.get(proj_name)
            if not proj:
                continue
            kind_str = proj.kind.name if hasattr(proj.kind, 'name') else str(proj.kind)
            deps = [d for d in proj.dependsOn if d in self.workspace.projects]
            build_order_info.append((proj_name, kind_str, deps))

        # Create build coordinator and print header
        toolchain_name = self.toolchain.name if self.toolchain else ""
        cache_status = getattr(self.workspace, '_cache_status', None)
        coordinator = BuildCoordinator(
            workspace_name=self.workspace.name,
            config=self.config,
            target_os=self.targetOs.value,
            target_arch=self.targetArch.value,
            toolchain=toolchain_name
        )
        coordinator.PrintHeader(build_order_info, cache_status)

        # Build each project
        success_count = 0
        fail_count = 0
        for proj_name in order:
            proj = self.workspace.projects.get(proj_name)
            if not proj:
                continue
            run_cwd = proj.location or self.workspace.location
            for cmd in proj.preBuildCommands:
                expanded_cmd = cmd
                if self._expander:
                    self._expander.SetProject(proj)
                    expanded_cmd = self._expander.Expand(cmd, recursive=True)
                Process.Run(expanded_cmd, shell=True, cwd=run_cwd)
            ok = self.BuildProject(proj)
            coordinator.MarkProjectBuilt(ok)
            for cmd in proj.postBuildCommands:
                expanded_cmd = cmd
                if self._expander:
                    self._expander.SetProject(proj)
                    expanded_cmd = self._expander.Expand(cmd, recursive=True)
                Process.Run(expanded_cmd, shell=True, cwd=run_cwd)
            if ok:
                success_count += 1
            else:
                fail_count += 1
                if not self.verbose:
                    break

        # Print footer
        coordinator.PrintFooter()

        if fail_count == 0:
            return 0
        else:
            return 1
