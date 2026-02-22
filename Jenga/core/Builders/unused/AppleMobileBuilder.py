import abc
import os
import plistlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from Jenga.Core.Api import (
    CompilerFamily, Project, ProjectKind, TargetArch, TargetEnv, TargetOS
)
from ...Utils import Colored, FileSystem, Process, Reporter
from ..Builder import Builder
from ..Platform import Platform


class AppleMobileBuilder(Builder, abc.ABC):
    """
    Classe de base pour les builders Apple mobiles (iOS, tvOS, watchOS).
    Fournit les méthodes communes : détection SDK, flags, version minimum, etc.
    """

    # Profils par cible
    _TARGETS: Dict[TargetOS, Dict[str, object]] = {
        TargetOS.IOS: {
            "display": "iOS",
            "sdk_device": "iphoneos",
            "sdk_simulator": "iphonesimulator",
            "triple_os": "ios",
            "min_flag": "mios-version-min",
            "platform_device": "iPhoneOS",
            "platform_simulator": "iPhoneSimulator",
            "requires_iphone_os": True,
            "device_family": [1, 2],          # iPhone, iPad
            "define": "IOS",
            "frameworks": ["Foundation", "UIKit"],
            "device_frameworks": ["OpenGLES"],
            "default_min": "12.0",
            "min_sdk_attr": "iosMinSdk",
        },
        TargetOS.TVOS: {
            "display": "tvOS",
            "sdk_device": "appletvos",
            "sdk_simulator": "appletvsimulator",
            "triple_os": "tvos",
            "min_flag": "mtvos-version-min",
            "platform_device": "AppleTVOS",
            "platform_simulator": "AppleTVSimulator",
            "requires_iphone_os": False,
            "device_family": [3],              # Apple TV
            "define": "TVOS",
            "frameworks": ["Foundation", "UIKit"],
            "device_frameworks": [],
            "default_min": "12.0",
            "min_sdk_attr": "tvosMinSdk",
        },
        TargetOS.WATCHOS: {
            "display": "watchOS",
            "sdk_device": "watchos",
            "sdk_simulator": "watchsimulator",
            "triple_os": "watchos",
            "min_flag": "mwatchos-version-min",
            "platform_device": "WatchOS",
            "platform_simulator": "WatchSimulator",
            "requires_iphone_os": False,
            "device_family": [4],              # Apple Watch
            "define": "WATCHOS",
            "frameworks": ["Foundation", "WatchKit"],
            "device_frameworks": [],
            "default_min": "8.0",
            "min_sdk_attr": "watchosMinSdk",
        },
        
        TargetOS.IPADOS: {
            "display": "iPadOS",
            "sdk_device": "iphoneos",           # même SDK qu'iOS
            "sdk_simulator": "iphonesimulator",
            "triple_os": "ios",                  # même triplet qu'iOS
            "min_flag": "mios-version-min",
            "platform_device": "iPhoneOS",
            "platform_simulator": "iPhoneSimulator",
            "requires_iphone_os": True,
            "device_family": [1, 2],             # iPhone, iPad (inchangé)
            "define": "IPADOS",
            "frameworks": ["Foundation", "UIKit"],
            "device_frameworks": ["OpenGLES"],
            "default_min": "13.0",                # version minimale recommandée
            "min_sdk_attr": "ipadosMinSdk",       # nouvel attribut
        },
        
        TargetOS.VISIONOS: {
            "display": "visionOS",
            "sdk_device": "xros",
            "sdk_simulator": "xrsimulator",
            "triple_os": "xros",
            "min_flag": "mxros-version-min",
            "platform_device": "XROS",
            "platform_simulator": "XRSimulator",
            "requires_iphone_os": False,
            "device_family": [7],                  # valeur Apple pour visionOS
            "define": "VISIONOS",
            "frameworks": ["Foundation", "SwiftUI", "RealityKit"],
            "device_frameworks": [],
            "default_min": "1.0",
            "min_sdk_attr": "visionosMinSdk",
        },
    }

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)

        if self.targetOs not in self._TARGETS:
            raise RuntimeError(f"Unsupported Apple mobile target: {self.targetOs.value}")

        self.target_profile = self._TARGETS[self.targetOs]
        self.is_simulator = self._IsSimulatorTarget()
        self.sdk_name = (
            str(self.target_profile["sdk_simulator"])
            if self.is_simulator else str(self.target_profile["sdk_device"])
        )
        self.sdk_path = self._GetSDKPath(self.sdk_name)
        if not self.sdk_path:
            raise RuntimeError(f"{self.target_profile['display']} SDK '{self.sdk_name}' not found.")

        self._CheckCompiler()
        self.min_version: str = ""  # sera définie dans BuildProject
        self.target_triple = self._GetTargetTriple()

    # -----------------------------------------------------------------------
    # Méthodes de base (communes)
    # -----------------------------------------------------------------------

    def _IsSimulatorTarget(self) -> bool:
        if self.targetArch in (TargetArch.X86_64, TargetArch.X86):
            return True
        platform_os = (self.platform or "").split("-", 1)[0].strip().lower()
        if "simulator" in platform_os:
            return True
        if self.targetEnv == TargetEnv.IOS and platform_os.endswith("sim"):
            return True
        return False

    def _GetArchName(self) -> str:
        return "arm64" if self.targetArch == TargetArch.ARM64 else "x86_64"

    def _GetSDKPath(self, sdk: str) -> Optional[Path]:
        try:
            result = Process.Capture(["xcrun", "--sdk", sdk, "--show-sdk-path"])
            return Path(result.strip())
        except Exception as e:
            Colored.PrintError(f"Failed to get SDK path for {sdk}: {e}")
            return None

    def _CheckCompiler(self) -> None:
        try:
            cc_path = Process.Capture(["xcrun", "--find", "clang"]).strip()
            cxx_path = Process.Capture(["xcrun", "--find", "clang++"]).strip()
            self.toolchain.ccPath = cc_path
            self.toolchain.cxxPath = cxx_path
            self.toolchain.compilerFamily = CompilerFamily.APPLE_CLANG
        except Exception as e:
            raise RuntimeError(f"Apple Clang not found. Install Xcode command line tools: {e}")

    def _GetMinimumVersion(self, project: Project) -> str:
        attr_map = {
            TargetOS.IOS: "iosMinSdk",
            TargetOS.TVOS: "tvosMinSdk",
            TargetOS.WATCHOS: "watchosMinSdk",
            TargetOS.IPADOS: "ipadosMinSdk",
            TargetOS.VISIONOS: "visionosMinSdk",
        }
        attr = attr_map.get(self.targetOs)
        if attr:
            min_ver = getattr(project, attr, None)
            if min_ver:
                return str(min_ver)
        return str(self.target_profile["default_min"])

    def _GetMinVersionArg(self) -> str:
        return f"-{self.target_profile['min_flag']}={self.min_version}"

    def _GetTargetTriple(self) -> str:
        arch = self._GetArchName()
        os_part = str(self.target_profile["triple_os"])
        suffix = "-simulator" if self.is_simulator else ""
        return f"{arch}-apple-{os_part}{self.min_version}{suffix}"

    def _GetTargetFlags(self) -> List[str]:
        return [
            "-target", self.target_triple,
            "-isysroot", str(self.sdk_path),
            self._GetMinVersionArg(),
        ]

    def _GetCommonCompilerFlags(self, project: Project) -> List[str]:
        flags: List[str] = []

        # Includes
        for inc in project.includeDirs:
            flags.append(f"-I{self.ResolveProjectPath(project, inc)}")

        # Définitions
        for define in getattr(self.toolchain, "defines", []):
            flags.append(f"-D{define}")
        for define in project.defines:
            flags.append(f"-D{define}")
        flags.append(f"-D{self.target_profile['define']}")
        if self.is_simulator:
            flags.append("-D__SIMULATOR__")

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
        elif warn == "Everything":
            flags.append("-Weverything")
        elif warn == "Error":
            flags.append("-Werror")

        # Standard / dialecte
        if project.language.value in ("C++", "Objective-C++"):
            if project.cppdialect:
                flags.append(f"-std={project.cppdialect.lower()}")
            flags.extend(getattr(self.toolchain, "cxxflags", []))
            flags.extend(project.cxxflags)
        else:
            if project.cdialect:
                flags.append(f"-std={project.cdialect.lower()}")
            flags.extend(getattr(self.toolchain, "cflags", []))
            flags.extend(project.cflags)

        # Objective-C
        if project.language.value in ("Objective-C", "Objective-C++"):
            flags.append("-ObjC")

        # Position Independent Code pour les libs partagées
        if project.kind == ProjectKind.SHARED_LIB:
            flags.append("-fPIC")

        return flags

    def _GetFrameworkLinkerArgs(self, project: Project) -> List[str]:
        args: List[str] = []
        # Frameworks du profil
        for fw in self.target_profile.get("frameworks", []):
            args.extend(["-framework", fw])
        if not self.is_simulator:
            for fw in self.target_profile.get("device_frameworks", []):
                args.extend(["-framework", fw])
        # Frameworks du projet
        for fw in project.frameworks:
            args.extend(["-framework", fw])
        # Frameworks de la toolchain
        for fw in getattr(self.toolchain, "frameworks", []):
            args.extend(["-framework", fw])
        # Framework paths
        for fw_path in getattr(self.toolchain, "frameworkPaths", []):
            args.append(f"-F{fw_path}")
        return args

    def _GetLibraryLinkerArgs(self, project: Project) -> List[str]:
        args: List[str] = []
        # Répertoires de libs
        for libdir in project.libDirs:
            args.append(f"-L{self.ResolveProjectPath(project, libdir)}")
        # Bibliothèques
        for lib in project.links:
            if self._IsDirectLibPath(lib):
                args.append(self.ResolveProjectPath(project, lib))
            else:
                args.append(f"-l{lib}")
        return args

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        p = Path(lib)
        return p.suffix in (".a", ".dylib", ".so", ".framework", ".lib") or "/" in lib or "\\" in lib or p.is_absolute()

    @staticmethod
    def _EnumValue(v):
        return v.value if hasattr(v, "value") else v

    # -----------------------------------------------------------------------
    # Méthodes abstraites à implémenter par les sous-classes
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
        pass

    # -----------------------------------------------------------------------
    # BuildProject (commun)
    # -----------------------------------------------------------------------

    def BuildProject(self, project: Project) -> bool:
        if Platform.GetHostOS() != TargetOS.MACOS:
            raise RuntimeError(f"{self.target_profile['display']} builds require macOS with Xcode command line tools.")

        # Récupération de la version minimale (doit être faite avant toute utilisation)
        self.min_version = self._GetMinimumVersion(project)

        # Appel à la méthode parente (qui gère l'application des filtres, la collecte des sources, etc.)
        return super().BuildProject(project)