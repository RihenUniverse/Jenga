#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apple Mobile Xcode Builder.
Builds iOS/tvOS/watchOS using xcodebuild (project generation + build/archive/export).
"""

import plistlib
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from Jenga.Core.Api import Project, ProjectKind, TargetArch, TargetEnv, TargetOS
from ...Utils import Colored, FileSystem, Process, Reporter
from ..Builder import Builder
from ..Platform import Platform


class XcodeProjectGenerator:
    """
    Generate a minimal .xcodeproj from a Jenga project.
    """

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        p = Path(lib)
        return p.suffix in (".a", ".dylib", ".so", ".framework", ".lib") or "/" in lib or "\\" in lib or p.is_absolute()

    @staticmethod
    def Generate(
        project: Project,
        target_os: TargetOS,
        target_arch: TargetArch,
        is_simulator: bool,
        build_dir: Path,
        target_profile: Dict[str, object],
        workspace: Optional[object] = None,  # pour résoudre les dépendances
    ) -> Optional[Path]:
        proj_name = project.targetName or project.name
        proj_dir = build_dir / f"{proj_name}.xcodeproj"
        FileSystem.RemoveDirectory(proj_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(proj_dir)

        XcodeProjectGenerator._WritePbxproj(project, target_os, target_arch, is_simulator, proj_dir, target_profile, workspace)
        XcodeProjectGenerator._WriteScheme(project, proj_name, proj_dir)
        XcodeProjectGenerator._WriteWorkspaceSettings(proj_dir)

        src_dir = proj_dir.parent / proj_name
        FileSystem.MakeDirectory(src_dir)
        XcodeProjectGenerator._CopySourceFiles(project, src_dir)

        info_plist = XcodeProjectGenerator._GenerateInfoPlist(project, target_os, is_simulator, src_dir, target_profile)
        if not info_plist:
            return None

        if project.links or project.frameworks:
            XcodeProjectGenerator._GeneratePodfile(project, src_dir, str(target_profile["cocoapods_platform"]))
        return proj_dir

    @staticmethod
    def _WritePbxproj(
        project: Project,
        target_os: TargetOS,
        target_arch: TargetArch,
        is_simulator: bool,
        proj_dir: Path,
        target_profile: Dict[str, object],
        workspace: Optional[object],
    ) -> None:
        proj_id = uuid.uuid4().hex.upper()[:24]
        target_id = uuid.uuid4().hex.upper()[:24]
        build_conf_id = uuid.uuid4().hex.upper()[:24]

        pbxproj = {
            "archiveVersion": "1",
            "classes": {},
            "objectVersion": "50",
            "objects": {
                proj_id: {
                    "isa": "PBXProject",
                    "attributes": {
                        "LastUpgradeCheck": "1430",
                        "TargetAttributes": {
                            target_id: {"CreatedOnToolsVersion": "14.3.1"}
                        },
                    },
                    "buildConfigurationList": build_conf_id,
                    "compatibilityVersion": "Xcode 14.0",
                    "developmentRegion": "en",
                    "hasScannedForEncodings": "0",
                    "knownRegions": ["en", "Base"],
                    "mainGroup": XcodeProjectGenerator._GetMainGroup(proj_dir.parent.name),
                    "productRefGroup": XcodeProjectGenerator._GetProductGroup(),
                    "projectDirPath": "",
                    "projectRoot": "",
                    "targets": [target_id],
                },
                target_id: {
                    "isa": "PBXNativeTarget",
                    "buildConfigurationList": XcodeProjectGenerator._GetBuildConfigurationList(project, target_profile),
                    "buildPhases": XcodeProjectGenerator._GetBuildPhases(),
                    "buildRules": [],
                    "dependencies": XcodeProjectGenerator._GetDependencies(project, workspace, proj_dir.parent),
                    "name": project.targetName or project.name,
                    "productName": project.targetName or project.name,
                    "productReference": XcodeProjectGenerator._GetProductReference(),
                    "productType": (
                        "com.apple.product-type.application"
                        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP)
                        else "com.apple.product-type.library.static"
                    ),
                },
            },
            "rootObject": proj_id,
        }

        proj_path = proj_dir / "project.pbxproj"
        with open(proj_path, "wb") as f:
            plistlib.dump(pbxproj, f, fmt=plistlib.FMT_XML)

    @staticmethod
    def _GetMainGroup(project_name: str) -> Dict:
        return {
            "isa": "PBXGroup",
            "children": [],
            "sourceTree": "<group>",
            "name": project_name,
        }

    @staticmethod
    def _GetProductGroup() -> Dict:
        return {
            "isa": "PBXGroup",
            "children": [],
            "name": "Products",
            "sourceTree": "<group>",
        }

    @staticmethod
    def _GetBuildConfigurationList(project: Project, target_profile: Dict[str, object]) -> Dict:
        return {
            "isa": "XCConfigurationList",
            "buildConfigurations": [
                XcodeProjectGenerator._GetBuildConfiguration("Debug", project, target_profile),
                XcodeProjectGenerator._GetBuildConfiguration("Release", project, target_profile),
            ],
            "defaultConfigurationIsVisible": "0",
            "defaultConfigurationName": "Debug",
        }

    @staticmethod
    def _GetBuildConfiguration(name: str, project: Project, target_profile: Dict[str, object]) -> Dict:
        return {
            "isa": "XCBuildConfiguration",
            "name": name,
            "buildSettings": XcodeProjectGenerator._GetBuildSettings(name, project, target_profile),
        }

    @staticmethod
    def _GetBuildSettings(config: str, project: Project, target_profile: Dict[str, object]) -> Dict:
        deployment_key = str(target_profile["deployment_key"])
        settings = {
            "ALWAYS_SEARCH_USER_PATHS": "NO",
            "CLANG_ANALYZER_NONNULL": "YES",
            "CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION": "YES_AGGRESSIVE",
            "CLANG_CXX_LANGUAGE_STANDARD": project.cppdialect.lower() if project.cppdialect else "gnu++17",
            "CLANG_CXX_LIBRARY": "libc++",
            "CLANG_ENABLE_MODULES": "YES",
            "CLANG_ENABLE_OBJC_ARC": "YES",
            "COPY_PHASE_STRIP": "NO",
            "DEBUG_INFORMATION_FORMAT": "dwarf-with-dsym" if config == "Debug" else "dwarf",
            "ENABLE_NS_ASSERTIONS": "YES" if config == "Debug" else "NO",
            "GCC_C_LANGUAGE_STANDARD": project.cdialect.lower() if project.cdialect else "gnu11",
            "MTL_ENABLE_DEBUG_INFO": "INCLUDE_SOURCE" if config == "Debug" else "NO",
            "MTL_FAST_MATH": "YES",
            "PRODUCT_NAME": project.targetName or project.name,
            deployment_key: project.iosMinSdk or str(target_profile["default_min"]),
            "SDKROOT": str(target_profile["sdk_device"] if not project._is_simulator else target_profile["sdk_simulator"]),
            "TARGETED_DEVICE_FAMILY": str(target_profile["device_family_setting"]),
        }

        if project.defines:
            settings["GCC_PREPROCESSOR_DEFINITIONS"] = project.defines + ["$(inherited)"]

        opt = project.optimize.value if hasattr(project.optimize, "value") else project.optimize
        if config == "Release":
            if opt == "Size":
                settings["GCC_OPTIMIZATION_LEVEL"] = "s"
            elif opt == "Speed":
                settings["GCC_OPTIMIZATION_LEVEL"] = "3"
            elif opt == "Full":
                settings["GCC_OPTIMIZATION_LEVEL"] = "fast"
            else:
                settings["GCC_OPTIMIZATION_LEVEL"] = "0"
        else:
            settings["GCC_OPTIMIZATION_LEVEL"] = "0"

        # Construction de OTHER_LDFLAGS avec gestion des frameworks et libs
        ldflags = []
        # Frameworks du projet
        for fw in project.frameworks:
            ldflags.extend(["-framework", fw])
        # Bibliothèques
        for lib in project.links:
            if XcodeProjectGenerator._IsDirectLibPath(lib):
                # Chemin absolu ou relatif : on le met tel quel
                ldflags.append(lib)
            else:
                ldflags.append(f"-l{lib}")
        if ldflags:
            settings["OTHER_LDFLAGS"] = ldflags

        return settings

    @staticmethod
    def _GetDependencies(project: Project, workspace: Optional[object], build_root: Path) -> List[Dict]:
        """Crée des dépendances vers d'autres projets Xcode (si présents)."""
        if not workspace or not hasattr(workspace, 'projects'):
            return []
        deps = []
        for dep_name in project.dependsOn:
            dep_proj = workspace.projects.get(dep_name)
            if not dep_proj:
                continue
            # Pour l'instant, on ne fait rien. Idéalement, il faudrait générer un sous-projet.
            # On se contente d'ajouter le chemin de la bibliothèque dans les flags.
            # On pourrait aussi créer une référence de produit et une dépendance de cible.
            # Complexe, on laisse pour plus tard.
        return []

    @staticmethod
    def _GetBuildPhases() -> List[Dict]:
        return [
            {
                "isa": "PBXSourcesBuildPhase",
                "buildActionMask": "2147483647",
                "files": [],
                "runOnlyForDeploymentPostprocessing": "0",
            },
            {
                "isa": "PBXFrameworksBuildPhase",
                "buildActionMask": "2147483647",
                "files": [],
                "runOnlyForDeploymentPostprocessing": "0",
            },
            {
                "isa": "PBXResourcesBuildPhase",
                "buildActionMask": "2147483647",
                "files": [],
                "runOnlyForDeploymentPostprocessing": "0",
            },
        ]

    @staticmethod
    def _GetProductReference() -> Dict:
        return {
            "isa": "PBXFileReference",
            "lastKnownFileType": "wrapper.application",
            "name": "app.app",
            "path": "app.app",
            "sourceTree": "BUILT_PRODUCTS_DIR",
        }

    @staticmethod
    def _WriteScheme(project: Project, proj_name: str, proj_dir: Path) -> None:
        scheme_dir = proj_dir / "xcshareddata" / "xcschemes"
        FileSystem.MakeDirectory(scheme_dir)
        scheme = f"""<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion = "1430" version = "1.7">
  <BuildAction parallelizeBuildables = "YES" buildImplicitDependencies = "YES">
    <BuildActionEntries>
      <BuildActionEntry buildForTesting = "YES" buildForRunning = "YES" buildForProfiling = "YES" buildForArchiving = "YES" buildForAnalyzing = "YES">
        <BuildableReference BuildableIdentifier = "primary" BlueprintIdentifier = "{proj_name}" BuildableName = "{project.targetName or proj_name}.app" BlueprintName = "{project.targetName or proj_name}" ReferencedContainer = "container:{proj_name}.xcodeproj" />
      </BuildActionEntry>
    </BuildActionEntries>
  </BuildAction>
  <TestAction buildConfiguration = "Debug" selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv = "YES">
    <Testables></Testables>
  </TestAction>
  <LaunchAction buildConfiguration = "Debug" selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB" launchStyle = "0" useCustomWorkingDirectory = "NO" ignoresPersistentStateOnLaunch = "NO" debugDocumentVersioning = "YES" debugServiceExtension = "internal" allowLocationSimulation = "YES">
    <BuildableProductRunnable runnableDebuggingMode = "0">
      <BuildableReference BuildableIdentifier = "primary" BlueprintIdentifier = "{proj_name}" BuildableName = "{project.targetName or proj_name}.app" BlueprintName = "{project.targetName or proj_name}" ReferencedContainer = "container:{proj_name}.xcodeproj" />
    </BuildableProductRunnable>
  </LaunchAction>
  <ProfileAction buildConfiguration = "Release" shouldUseLaunchSchemeArgsEnv = "YES" savedToolIdentifier = "" useCustomWorkingDirectory = "NO" debugDocumentVersioning = "YES">
    <BuildableProductRunnable runnableDebuggingMode = "0">
      <BuildableReference BuildableIdentifier = "primary" BlueprintIdentifier = "{proj_name}" BuildableName = "{project.targetName or proj_name}.app" BlueprintName = "{project.targetName or proj_name}" ReferencedContainer = "container:{proj_name}.xcodeproj" />
    </BuildableProductRunnable>
  </ProfileAction>
  <AnalyzeAction buildConfiguration = "Debug"></AnalyzeAction>
  <ArchiveAction buildConfiguration = "Release" revealArchiveInOrganizer = "YES"></ArchiveAction>
</Scheme>
"""
        (scheme_dir / f"{proj_name}.xcscheme").write_text(scheme, encoding="utf-8")

    @staticmethod
    def _WriteWorkspaceSettings(proj_dir: Path) -> None:
        settings_dir = proj_dir / "project.xcworkspace" / "xcshareddata"
        FileSystem.MakeDirectory(settings_dir)
        settings_path = settings_dir / "WorkspaceSettings.xcsettings"
        settings_path.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>BuildSystemType</key>
    <string>Original</string>
</dict>
</plist>
""",
            encoding="utf-8",
        )

    @staticmethod
    def _CopySourceFiles(project: Project, src_dir: Path) -> None:
        base = Path(project.location) if project.location else Path.cwd()
        for pattern in project.files:
            for f in FileSystem.ListFiles(base, pattern, recursive=True, fullPath=True):
                rel = Path(f).relative_to(base)
                dest = src_dir / rel
                FileSystem.MakeDirectory(dest.parent)
                shutil.copy2(f, dest)

    @staticmethod
    def _GenerateInfoPlist(
        project: Project,
        target_os: TargetOS,
        is_simulator: bool,
        src_dir: Path,
        target_profile: Dict[str, object],
    ) -> Optional[Path]:
        plist_path = src_dir / "Info.plist"
        bundle_id = project.iosBundleId or f"com.{project.name}"
        platform_name = (
            str(target_profile["platform_simulator"])
            if is_simulator else str(target_profile["platform_device"])
        )
        plist = {
            "CFBundleDevelopmentRegion": "$(DEVELOPMENT_LANGUAGE)",
            "CFBundleExecutable": "$(EXECUTABLE_NAME)",
            "CFBundleIdentifier": bundle_id,
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundleName": project.targetName or project.name,
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": project.iosVersion or "1.0",
            "CFBundleVersion": project.iosBuildNumber or "1",
            "CFBundleSupportedPlatforms": [platform_name],
            "UIDeviceFamily": list(target_profile["device_family_list"]),
        }
        if bool(target_profile["requires_iphone_os"]):
            plist["LSRequiresIPhoneOS"] = True
        if target_os == TargetOS.IOS:
            plist["UISupportedInterfaceOrientations"] = [
                "UIInterfaceOrientationPortrait",
                "UIInterfaceOrientationLandscapeLeft",
                "UIInterfaceOrientationLandscapeRight",
            ]
            plist["UISupportedInterfaceOrientations~ipad"] = [
                "UIInterfaceOrientationPortrait",
                "UIInterfaceOrientationPortraitUpsideDown",
                "UIInterfaceOrientationLandscapeLeft",
                "UIInterfaceOrientationLandscapeRight",
            ]
        with open(plist_path, "wb") as f:
            plistlib.dump(plist, f)
        return plist_path

    @staticmethod
    def _GeneratePodfile(project: Project, src_dir: Path, platform_name: str) -> None:
        pods = [dep[4:] for dep in project.links if dep.startswith("pod:")]
        if not pods and not project.frameworks:
            return
        pod_lines = "\n".join([f"  pod '{pod}'" for pod in pods])
        podfile_content = f"""
platform :{platform_name}, '{project.iosMinSdk or '12.0'}'

target '{project.targetName or project.name}' do
  use_frameworks!
{pod_lines}
end
"""
        (src_dir / "Podfile").write_text(podfile_content.strip() + "\n", encoding="utf-8")


class XcodeIOSBuilder(Builder):
    """
    Apple mobile builder using Xcode/xcodebuild.
    """

    _TARGETS: Dict[TargetOS, Dict[str, object]] = {
        TargetOS.IOS: {
            "display": "iOS",
            "sdk_device": "iphoneos",
            "sdk_simulator": "iphonesimulator",
            "deployment_key": "IPHONEOS_DEPLOYMENT_TARGET",
            "sdk_device_root": "iphoneos",
            "device_family_setting": "1,2",
            "device_family_list": [1, 2],
            "platform_device": "iPhoneOS",
            "platform_simulator": "iPhoneSimulator",
            "requires_iphone_os": True,
            "cocoapods_platform": "ios",
            "default_min": "12.0",
        },
        TargetOS.TVOS: {
            "display": "tvOS",
            "sdk_device": "appletvos",
            "sdk_simulator": "appletvsimulator",
            "deployment_key": "TVOS_DEPLOYMENT_TARGET",
            "sdk_device_root": "appletvos",
            "device_family_setting": "3",
            "device_family_list": [3],
            "platform_device": "AppleTVOS",
            "platform_simulator": "AppleTVSimulator",
            "requires_iphone_os": False,
            "cocoapods_platform": "tvos",
            "default_min": "12.0",
        },
        TargetOS.WATCHOS: {
            "display": "watchOS",
            "sdk_device": "watchos",
            "sdk_simulator": "watchsimulator",
            "deployment_key": "WATCHOS_DEPLOYMENT_TARGET",
            "sdk_device_root": "watchos",
            "device_family_setting": "4",
            "device_family_list": [4],
            "platform_device": "WatchOS",
            "platform_simulator": "WatchSimulator",
            "requires_iphone_os": False,
            "cocoapods_platform": "watchos",
            "default_min": "8.0",
        },
    }

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)

        if Platform.GetHostOS() != TargetOS.MACOS:
            raise RuntimeError("Apple mobile builds require macOS with Xcode.")
        if self.targetOs not in self._TARGETS:
            raise RuntimeError(f"Unsupported Apple mobile target for xcode builder: {self.targetOs.value}")

        self.target_profile = self._TARGETS[self.targetOs]
        self.is_simulator = self._IsSimulatorTarget()
        self.sdk = (
            str(self.target_profile["sdk_simulator"])
            if self.is_simulator else str(self.target_profile["sdk_device"])
        )
        self.configuration = self.config.capitalize() if self.config else "Debug"
        self.xcode_version = ""
        self.signing_identity: Optional[str] = None
        self.provisioning_profile: Optional[str] = None

        self._CheckXcode()
        # Ne pas appeler _ResolveSigningIdentity ici car on n'a pas le projet

    def _CheckXcode(self) -> None:
        try:
            version = Process.Capture(["xcodebuild", "-version"])
            if not version:
                raise RuntimeError("xcodebuild not found")
            self.xcode_version = version.strip().split("\n")[0]
        except Exception as e:
            raise RuntimeError(f"Xcode is required for Apple mobile builds: {e}")

    def _ResolveSigningIdentity(self, project: Project) -> None:
        """Récupère les infos de signature depuis le projet."""
        self.signing_identity = project.iosSigningIdentity or None
        self.provisioning_profile = project.iosProvisioningProfile or None

    def _IsSimulatorTarget(self) -> bool:
        if self.targetArch in (TargetArch.X86_64, TargetArch.X86):
            return True
        platform_os = (self.platform or "").split("-", 1)[0].strip().lower()
        if "simulator" in platform_os:
            return True
        if self.targetEnv == TargetEnv.IOS and platform_os.endswith("sim"):
            return True
        return False

    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"
        if project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        return ".app"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        raise NotImplementedError("Direct compilation is not used in xcode mode.")

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        if not self.IsModuleFile(sourceFile):
            return []
        return ["-fmodules", "-fcxx-modules", "-std=c++20"]

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        raise NotImplementedError("Direct linking is not used in xcode mode.")

    def BuildProject(self, project: Project) -> bool:
        Reporter.Info(f"Building {self.target_profile['display']} project {project.name} ({self.sdk})")

        # Initialiser les infos de signature
        self._ResolveSigningIdentity(project)

        project._jengaLastArchivePath = ""
        project._jengaLastIpaPath = ""

        build_root = Path(self.GetTargetDir(project)) / f"{self.target_profile['cocoapods_platform']}-build"
        FileSystem.MakeDirectory(build_root)

        # Ajouter un flag au projet pour savoir s'il est simulateur (utilisé dans le générateur)
        project._is_simulator = self.is_simulator

        xcode_proj = XcodeProjectGenerator.Generate(
            project=project,
            target_os=self.targetOs,
            target_arch=self.targetArch,
            is_simulator=self.is_simulator,
            build_dir=build_root,
            target_profile=self.target_profile,
            workspace=self.workspace,
        )
        if not xcode_proj:
            Reporter.Error("Failed to generate Xcode project")
            return False

        self._InstallCocoaPodsIfNeeded(xcode_proj)

        if not self._RunXcodeBuild(xcode_proj, project):
            return False

        app_bundle = xcode_proj.parent / "build" / f"{project.targetName or project.name}.app"
        project._jengaLastAppBundle = str(app_bundle) if app_bundle.exists() else ""

        if not self.is_simulator:
            archive_path = self._ArchiveProject(xcode_proj, project, build_root)
            if not archive_path:
                return False
            project._jengaLastArchivePath = str(archive_path)

            ipa_path = self._ExportIPA(archive_path, project, build_root)
            if ipa_path:
                project._jengaLastIpaPath = str(ipa_path)
                Reporter.Success(f"IPA generated: {ipa_path}")
            else:
                Reporter.Warning("IPA export failed, archive created only.")

        return True

    def _InstallCocoaPodsIfNeeded(self, xcode_proj: Path) -> None:
        podfile = xcode_proj.parent / xcode_proj.stem / "Podfile"
        if not podfile.exists():
            return
        Reporter.Info("Installing CocoaPods dependencies...")
        result = Process.ExecuteCommand(["pod", "install"], cwd=podfile.parent, captureOutput=False, silent=False)
        if result.returnCode != 0:
            Reporter.Warning("pod install failed, continuing without pods.")

    def _RunXcodeBuild(self, xcode_proj: Path, project: Project) -> bool:
        scheme = project.targetName or xcode_proj.stem
        derived_data = xcode_proj.parent / "DerivedData"

        args = [
            "xcodebuild",
            "-project", str(xcode_proj),
            "-scheme", scheme,
            "-configuration", self.configuration,
            "-sdk", self.sdk,
            "CONFIGURATION_BUILD_DIR=" + str(xcode_proj.parent / "build"),
            "OBJROOT=" + str(derived_data / "Objects"),
            "SYMROOT=" + str(derived_data / "Symbols"),
            "SHARED_PRECOMPS_DIR=" + str(derived_data / "PrecompiledHeaders"),
        ]

        if not self.is_simulator:
            if self.signing_identity:
                args.append(f'CODE_SIGN_IDENTITY="{self.signing_identity}"')
            if self.provisioning_profile:
                args.append(f'PROVISIONING_PROFILE_SPECIFIER="{self.provisioning_profile}"')
            else:
                args.append('CODE_SIGN_IDENTITY=""')
                args.append("CODE_SIGNING_REQUIRED=NO")
                args.append("CODE_SIGNING_ALLOWED=NO")

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def _ArchiveProject(self, xcode_proj: Path, project: Project, build_root: Path) -> Optional[Path]:
        scheme = project.targetName or xcode_proj.stem
        archive_path = build_root / f"{scheme}.xcarchive"
        args = [
            "xcodebuild",
            "-project", str(xcode_proj),
            "-scheme", scheme,
            "-configuration", self.configuration,
            "-sdk", self.sdk,
            "-archivePath", str(archive_path),
            "archive",
        ]
        result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
        if result.returnCode == 0:
            return archive_path
        return None

    def _ExportIPA(self, archive_path: Path, project: Project, build_root: Path) -> Optional[Path]:
        export_dir = build_root / "IPA"
        FileSystem.RemoveDirectory(export_dir, recursive=True, ignoreErrors=True)
        export_plist = self._GenerateExportOptionsPlist(project, export_dir)
        args = [
            "xcodebuild",
            "-exportArchive",
            "-archivePath", str(archive_path),
            "-exportPath", str(export_dir),
            "-exportOptionsPlist", str(export_plist),
            "-allowProvisioningUpdates",
        ]
        result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
        if result.returnCode != 0:
            return None
        ipa_files = list(export_dir.glob("*.ipa"))
        return ipa_files[0] if ipa_files else None

    def _GenerateExportOptionsPlist(self, project: Project, export_dir: Path) -> Path:
        FileSystem.MakeDirectory(export_dir)
        method = "development"
        if project.iosDistributionType == "app-store":
            method = "app-store"
        elif project.iosDistributionType == "ad-hoc":
            method = "ad-hoc"
        elif project.iosDistributionType == "enterprise":
            method = "enterprise"

        options = {
            "method": method,
            "teamID": project.iosTeamId or "",
            "signingStyle": "manual" if (project.iosProvisioningProfile or self.provisioning_profile) else "automatic",
            "stripSwiftSymbols": True,
            "compileBitcode": False,
            "thinning": "<none>",
        }
        if project.iosBundleId:
            options["provisioningProfiles"] = {
                project.iosBundleId: project.iosProvisioningProfile or self.provisioning_profile or ""
            }
        plist_path = export_dir / "ExportOptions.plist"
        with open(plist_path, "wb") as f:
            plistlib.dump(options, f)
        return plist_path

    @staticmethod
    def _CreateIpaFromBundle(app_bundle: Path, output_ipa: Path) -> Optional[Path]:
        if not app_bundle.exists():
            return None
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            payload_dir = tmp / "Payload"
            FileSystem.MakeDirectory(payload_dir)
            bundle_copy = payload_dir / app_bundle.name
            shutil.copytree(app_bundle, bundle_copy, dirs_exist_ok=True)
            zip_path = tmp / f"{output_ipa.stem}.zip"
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for entry in payload_dir.rglob("*"):
                    zf.write(entry, entry.relative_to(tmp))
            shutil.copy2(zip_path, output_ipa)
        return output_ipa

    def ExportIPA(self, app_bundle: Path, project: Project) -> Optional[Path]:
        cached = Path(str(getattr(project, "_jengaLastIpaPath", "") or ""))
        if cached and cached.exists():
            return cached

        if self.is_simulator:
            output_ipa = Path(app_bundle).parent / f"{project.targetName or project.name}.ipa"
            return self._CreateIpaFromBundle(Path(app_bundle), output_ipa)

        if not self.BuildProject(project):
            return None
        cached = Path(str(getattr(project, "_jengaLastIpaPath", "") or ""))
        if cached and cached.exists():
            return cached
        Colored.PrintError("IPA export failed after build.")
        return None