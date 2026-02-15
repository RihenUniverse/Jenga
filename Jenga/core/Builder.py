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
            self._expander.SetConfig({
                'name': config,
                'buildcfg': config,
                'platform': platform,
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

        # Auto-wire local library dependencies for link phase.
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
            if dep_out not in project.links:
                project.links.append(dep_out)
            project.links = [l for l in project.links if l != dep_name]

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
