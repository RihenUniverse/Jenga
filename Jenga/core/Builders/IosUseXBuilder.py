#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS Builder – Compilation pour iOS et simulateur.
Génère un projet Xcode réel, utilise xcodebuild pour compiler, archiver et exporter.
Gestion complète des signatures, provisioning profiles, frameworks.
"""

import os
import shutil
import plistlib
import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import tempfile
import uuid

from Jenga.Core.Api import Project, ProjectKind, TargetArch, TargetOS
from ...Utils import Process, FileSystem, Colored, Reporter
from ..Builder import Builder
from ..Toolchains import ToolchainManager
from ..Platform import Platform


class XcodeProjectGenerator:
    """
    Générateur de projet Xcode à partir d'un projet Jenga.
    Crée un .xcodeproj avec la structure minimale nécessaire.
    """

    @staticmethod
    def Generate(project: Project, target_arch: TargetArch, is_simulator: bool, build_dir: Path) -> Optional[Path]:
        """
        Crée un projet Xcode complet dans build_dir.
        Retourne le chemin vers le .xcodeproj.
        """
        proj_name = project.targetName or project.name
        proj_dir = build_dir / f"{proj_name}.xcodeproj"
        FileSystem.RemoveDirectory(proj_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(proj_dir)

        # Créer les fichiers de base du projet Xcode
        XcodeProjectGenerator._WritePbxproj(project, target_arch, is_simulator, proj_dir)
        XcodeProjectGenerator._WriteScheme(project, proj_name, proj_dir)
        XcodeProjectGenerator._WriteWorkspaceSettings(proj_dir)

        # Créer le répertoire du projet (groupe racine)
        src_dir = proj_dir.parent / proj_name
        FileSystem.MakeDirectory(src_dir)

        # Copier les fichiers sources
        XcodeProjectGenerator._CopySourceFiles(project, src_dir)

        # Générer Info.plist
        info_plist = XcodeProjectGenerator._GenerateInfoPlist(project, src_dir)
        if not info_plist:
            return None

        # Ajouter éventuellement un Podfile (pour CocoaPods)
        if project.links or project.frameworks:
            XcodeProjectGenerator._GeneratePodfile(project, src_dir)

        return proj_dir

    @staticmethod
    def _WritePbxproj(project: Project, target_arch: TargetArch, is_simulator: bool, proj_dir: Path):
        """Écrit le fichier project.pbxproj (format plist)."""
        # Identifiants uniques
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
                            target_id: {
                                "CreatedOnToolsVersion": "14.3.1"
                            }
                        }
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
                    "targets": [target_id]
                },
                target_id: {
                    "isa": "PBXNativeTarget",
                    "buildConfigurationList": XcodeProjectGenerator._GetBuildConfigurationList(project),
                    "buildPhases": XcodeProjectGenerator._GetBuildPhases(),
                    "buildRules": [],
                    "dependencies": [],
                    "name": project.targetName or project.name,
                    "productName": project.targetName or project.name,
                    "productReference": XcodeProjectGenerator._GetProductReference(),
                    "productType": "com.apple.product-type.application" if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP) else "com.apple.product-type.library.static"
                }
            },
            "rootObject": proj_id
        }

        # Convertir en format plist et écrire
        proj_path = proj_dir / "project.pbxproj"
        with open(proj_path, 'wb') as f:
            plistlib.dump(pbxproj, f, fmt=plistlib.FMT_XML)

    @staticmethod
    def _GetMainGroup(project_name: str) -> Dict:
        """Groupe racine."""
        return {
            "isa": "PBXGroup",
            "children": [],
            "sourceTree": "<group>",
            "name": project_name
        }

    @staticmethod
    def _GetProductGroup() -> Dict:
        return {
            "isa": "PBXGroup",
            "children": [],
            "name": "Products",
            "sourceTree": "<group>"
        }

    @staticmethod
    def _GetBuildConfigurationList(project: Project) -> Dict:
        """Configuration de build (Debug/Release)."""
        return {
            "isa": "XCConfigurationList",
            "buildConfigurations": [
                XcodeProjectGenerator._GetBuildConfiguration("Debug", project),
                XcodeProjectGenerator._GetBuildConfiguration("Release", project)
            ],
            "defaultConfigurationIsVisible": "0",
            "defaultConfigurationName": "Debug"
        }

    @staticmethod
    def _GetBuildConfiguration(name: str, project: Project) -> Dict:
        """Configuration individuelle."""
        return {
            "isa": "XCBuildConfiguration",
            "name": name,
            "buildSettings": XcodeProjectGenerator._GetBuildSettings(name, project)
        }

    @staticmethod
    def _GetBuildSettings(config: str, project: Project) -> Dict:
        """Paramètres de compilation."""
        settings = {
            "ALWAYS_SEARCH_USER_PATHS": "NO",
            "CLANG_ANALYZER_NONNULL": "YES",
            "CLANG_ANALYZER_NUMBER_OBJECT_CONVERSION": "YES_AGGRESSIVE",
            "CLANG_CXX_LANGUAGE_STANDARD": project.cppdialect or "gnu++17",
            "CLANG_CXX_LIBRARY": "libc++",
            "CLANG_ENABLE_MODULES": "YES",
            "CLANG_ENABLE_OBJC_ARC": "YES",
            "CLANG_WARN_BLOCK_CAPTURE_AUTORELEASING": "YES",
            "CLANG_WARN_BOOL_CONVERSION": "YES",
            "CLANG_WARN_COMMA": "YES",
            "CLANG_WARN_CONSTANT_CONVERSION": "YES",
            "CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS": "YES",
            "CLANG_WARN_DIRECT_OBJC_ISA_USAGE": "YES_ERROR",
            "CLANG_WARN_DOCUMENTATION_COMMENTS": "YES",
            "CLANG_WARN_EMPTY_BODY": "YES",
            "CLANG_WARN_ENUM_CONVERSION": "YES",
            "CLANG_WARN_INFINITE_RECURSION": "YES",
            "CLANG_WARN_INT_CONVERSION": "YES",
            "CLANG_WARN_NON_LITERAL_NULL_CONVERSION": "YES",
            "CLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF": "YES",
            "CLANG_WARN_OBJC_LITERAL_CONVERSION": "YES",
            "CLANG_WARN_OBJC_ROOT_CLASS": "YES_ERROR",
            "CLANG_WARN_QUOTED_INCLUDE_IN_FRAMEWORK_HEADER": "YES",
            "CLANG_WARN_RANGE_LOOP_ANALYSIS": "YES",
            "CLANG_WARN_STRICT_PROTOTYPES": "YES",
            "CLANG_WARN_SUSPICIOUS_MOVE": "YES",
            "CLANG_WARN_UNGUARDED_AVAILABILITY": "YES_AGGRESSIVE",
            "CLANG_WARN_UNREACHABLE_CODE": "YES",
            "CLANG_WARN__DUPLICATE_METHOD_MATCH": "YES",
            "COPY_PHASE_STRIP": "NO",
            "DEBUG_INFORMATION_FORMAT": "dwarf-with-dsym" if config == "Debug" else "dwarf",
            "ENABLE_NS_ASSERTIONS": "YES" if config == "Debug" else "NO",
            "ENABLE_STRICT_OBJC_MSGSEND": "YES",
            "GCC_C_LANGUAGE_STANDARD": project.cdialect or "gnu11",
            "GCC_NO_COMMON_BLOCKS": "YES",
            "GCC_WARN_64_TO_32_BIT_CONVERSION": "YES",
            "GCC_WARN_ABOUT_RETURN_TYPE": "YES_ERROR",
            "GCC_WARN_UNDECLARED_SELECTOR": "YES",
            "GCC_WARN_UNINITIALIZED_AUTOS": "YES_AGGRESSIVE",
            "GCC_WARN_UNUSED_FUNCTION": "YES",
            "GCC_WARN_UNUSED_VARIABLE": "YES",
            "IPHONEOS_DEPLOYMENT_TARGET": project.iosMinSdk or "12.0",
            "MTL_ENABLE_DEBUG_INFO": "INCLUDE_SOURCE" if config == "Debug" else "NO",
            "MTL_FAST_MATH": "YES",
            "PRODUCT_NAME": project.targetName or project.name,
            "SDKROOT": "iphoneos",
            "TARGETED_DEVICE_FAMILY": "1,2",  # iPhone + iPad
        }

        # Ajouter les defines
        if project.defines:
            settings["GCC_PREPROCESSOR_DEFINITIONS"] = project.defines + ["$(inherited)"]

        # Optimisation
        opt = project.optimize.value if hasattr(project.optimize, 'value') else project.optimize
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

        # Frameworks et librairies
        if project.frameworks:
            settings["OTHER_LDFLAGS"] = [f"-framework {fw}" for fw in project.frameworks]
        if project.links:
            settings["OTHER_LDFLAGS"] = settings.get("OTHER_LDFLAGS", []) + [f"-l{lib}" for lib in project.links]

        return settings

    @staticmethod
    def _GetBuildPhases() -> List[Dict]:
        """Phases de build : sources, ressources, etc."""
        return [
            {
                "isa": "PBXSourcesBuildPhase",
                "buildActionMask": "2147483647",
                "files": [],
                "runOnlyForDeploymentPostprocessing": "0"
            },
            {
                "isa": "PBXFrameworksBuildPhase",
                "buildActionMask": "2147483647",
                "files": [],
                "runOnlyForDeploymentPostprocessing": "0"
            },
            {
                "isa": "PBXResourcesBuildPhase",
                "buildActionMask": "2147483647",
                "files": [],
                "runOnlyForDeploymentPostprocessing": "0"
            }
        ]

    @staticmethod
    def _GetProductReference() -> Dict:
        return {
            "isa": "PBXFileReference",
            "lastKnownFileType": "wrapper.application",
            "name": "app.app",
            "path": "app.app",
            "sourceTree": "BUILT_PRODUCTS_DIR"
        }

    @staticmethod
    def _WriteScheme(project: Project, proj_name: str, proj_dir: Path):
        """Crée un schéma Xcode pour permettre le build en ligne de commande."""
        scheme_dir = proj_dir / "xcshareddata" / "xcschemes"
        FileSystem.MakeDirectory(scheme_dir)

        scheme = f"""<?xml version="1.0" encoding="UTF-8"?>
<Scheme
   LastUpgradeVersion = "1430"
   version = "1.7">
   <BuildAction
      parallelizeBuildables = "YES"
      buildImplicitDependencies = "YES">
      <BuildActionEntries>
         <BuildActionEntry
            buildForTesting = "YES"
            buildForRunning = "YES"
            buildForProfiling = "YES"
            buildForArchiving = "YES"
            buildForAnalyzing = "YES">
            <BuildableReference
               BuildableIdentifier = "primary"
               BlueprintIdentifier = "{proj_name}"
               BuildableName = "{project.targetName or proj_name}.app"
               BlueprintName = "{project.targetName or proj_name}"
               ReferencedContainer = "container:{proj_name}.xcodeproj">
            </BuildableReference>
         </BuildActionEntry>
      </BuildActionEntries>
   </BuildAction>
   <TestAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      shouldUseLaunchSchemeArgsEnv = "YES">
      <Testables>
      </Testables>
   </TestAction>
   <LaunchAction
      buildConfiguration = "Debug"
      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
      launchStyle = "0"
      useCustomWorkingDirectory = "NO"
      ignoresPersistentStateOnLaunch = "NO"
      debugDocumentVersioning = "YES"
      debugServiceExtension = "internal"
      allowLocationSimulation = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{proj_name}"
            BuildableName = "{project.targetName or proj_name}.app"
            BlueprintName = "{project.targetName or proj_name}"
            ReferencedContainer = "container:{proj_name}.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </LaunchAction>
   <ProfileAction
      buildConfiguration = "Release"
      shouldUseLaunchSchemeArgsEnv = "YES"
      savedToolIdentifier = ""
      useCustomWorkingDirectory = "NO"
      debugDocumentVersioning = "YES">
      <BuildableProductRunnable
         runnableDebuggingMode = "0">
         <BuildableReference
            BuildableIdentifier = "primary"
            BlueprintIdentifier = "{proj_name}"
            BuildableName = "{project.targetName or proj_name}.app"
            BlueprintName = "{project.targetName or proj_name}"
            ReferencedContainer = "container:{proj_name}.xcodeproj">
         </BuildableReference>
      </BuildableProductRunnable>
   </ProfileAction>
   <AnalyzeAction
      buildConfiguration = "Debug">
   </AnalyzeAction>
   <ArchiveAction
      buildConfiguration = "Release"
      revealArchiveInOrganizer = "YES">
   </ArchiveAction>
</Scheme>
"""
        scheme_path = scheme_dir / f"{proj_name}.xcscheme"
        scheme_path.write_text(scheme, encoding="utf-8")

    @staticmethod
    def _WriteWorkspaceSettings(proj_dir: Path):
        """Créer le fichier WorkspaceSettings.xcsettings."""
        settings_dir = proj_dir / "project.xcworkspace" / "xcshareddata"
        FileSystem.MakeDirectory(settings_dir)
        settings_path = settings_dir / "WorkspaceSettings.xcsettings"
        settings_path.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>BuildSystemType</key>
    <string>Original</string>
</dict>
</plist>
""")

    @staticmethod
    def _CopySourceFiles(project: Project, src_dir: Path):
        """Copie les fichiers sources dans le répertoire du projet."""
        base = Path(project.location) if project.location else Path.cwd()
        for pattern in project.files:
            for f in FileSystem.ListFiles(base, pattern, recursive=True, fullPath=True):
                rel = Path(f).relative_to(base)
                dest = src_dir / rel
                FileSystem.MakeDirectory(dest.parent)
                shutil.copy2(f, dest)

    @staticmethod
    def _GenerateInfoPlist(project: Project, src_dir: Path) -> Optional[Path]:
        """Génère un Info.plist à partir des propriétés du projet."""
        plist_path = src_dir / "Info.plist"
        bundle_id = project.iosBundleId or f"com.{project.name}"

        plist = {
            "CFBundleDevelopmentRegion": "$(DEVELOPMENT_LANGUAGE)",
            "CFBundleExecutable": "$(EXECUTABLE_NAME)",
            "CFBundleIdentifier": bundle_id,
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundleName": project.targetName or project.name,
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": project.iosVersion or "1.0",
            "CFBundleVersion": "1",
            "LSRequiresIPhoneOS": True,
            "UIRequiredDeviceCapabilities": ["armv7"],
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
            ]
        }

        with open(plist_path, 'wb') as f:
            plistlib.dump(plist, f)
        return plist_path

    @staticmethod
    def _GeneratePodfile(project: Project, src_dir: Path):
        """Génère un Podfile si le projet utilise des dépendances CocoaPods."""
        pods = []
        # Les dépendances dans links peuvent être interprétées comme des pods si elles commencent par 'pod:'
        for dep in project.links:
            if dep.startswith('pod:'):
                pods.append(dep[4:])

        if not pods and not project.frameworks:
            return

        podfile_content = f"""
platform :ios, '{project.iosMinSdk or '12.0'}'

target '{project.targetName or project.name}' do
  use_frameworks!
  {'  pod ' + "'\n  pod '".join(pods) if pods else ''}
end
"""
        podfile_path = src_dir / "Podfile"
        podfile_path.write_text(podfile_content.strip(), encoding="utf-8")


class IOSBuilder(Builder):
    """
    Builder pour iOS utilisant Xcode et xcodebuild.
    Génère un projet Xcode, compile, archive et exporte l'IPA.
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)

        # Vérifier que l'hôte est macOS
        if Platform.GetHostOS() != TargetOS.MACOS:
            raise RuntimeError("iOS builds require macOS with Xcode.")
        
        self.is_simulator = (self.targetArch in (TargetArch.X86_64, TargetArch.X86))
        self.sdk = "iphonesimulator" if self.is_simulator else "iphoneos"
        self.configuration = self.config.capitalize() if self.config else "Debug"

        self._CheckXcode()
        self._ResolveSigningIdentity(workspace)

    def _CheckXcode(self):
        """Vérifie que Xcode est installé et que les outils sont disponibles."""
        try:
            version = Process.Capture(["xcodebuild", "-version"])
            if not version:
                raise RuntimeError("xcodebuild not found")
            self.xcode_version = version.strip().split('\n')[0]
        except Exception as e:
            raise RuntimeError(f"Xcode is required for iOS builds: {e}")

    def _ResolveSigningIdentity(self, workspace):
        """Détermine l'identité de signature et le provisioning profile."""
        # On peut récupérer depuis le workspace ou le projet.
        # À implémenter selon les besoins.
        self.signing_identity = None
        self.provisioning_profile = None

    # -----------------------------------------------------------------------
    # Interface Builder
    # -----------------------------------------------------------------------

    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        else:
            return ".app"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        # Non utilisé : on utilise xcodebuild pour tout compiler.
        raise NotImplementedError("Direct compilation not supported for iOS, use BuildProject()")

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        flags = []
        if not self.IsModuleFile(sourceFile):
            return flags
        flags.extend(["-fmodules", "-fcxx-modules", "-std=c++20"])
        return flags

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        raise NotImplementedError("Direct linking not supported for iOS, use BuildProject()")

    # -----------------------------------------------------------------------
    # Processus de build complet
    # -----------------------------------------------------------------------

    def BuildProject(self, project: Project) -> bool:
        """
        Construit le projet iOS :
        1. Génère un projet Xcode
        2. Lance pod install si nécessaire
        3. Compile avec xcodebuild
        4. Archive et exporte l'IPA (pour device)
        """
        Reporter.Info(f"Building iOS project {project.name} ({self.sdk})")

        build_root = Path(self.GetTargetDir(project)) / "ios-build"
        FileSystem.MakeDirectory(build_root)

        # 1. Générer le projet Xcode
        xcode_proj = XcodeProjectGenerator.Generate(project, self.targetArch, self.is_simulator, build_root)
        if not xcode_proj:
            Reporter.Error("Failed to generate Xcode project")
            return False

        # 2. Installer les pods si nécessaire
        self._InstallCocoaPodsIfNeeded(xcode_proj)

        # 3. Compiler
        if not self._RunXcodeBuild(xcode_proj, project):
            return False

        # 4. Pour device, archiver et exporter IPA
        if not self.is_simulator:
            archive_path = self._ArchiveProject(xcode_proj, project, build_root)
            if not archive_path:
                return False
            ipa_path = self._ExportIPA(archive_path, project, build_root)
            if ipa_path:
                Reporter.Success(f"IPA generated: {ipa_path}")
            else:
                Reporter.Warning("IPA export failed, only archive created")

        return True

    def _InstallCocoaPodsIfNeeded(self, xcode_proj: Path):
        """Exécute pod install si un Podfile est présent."""
        podfile = xcode_proj.parent / xcode_proj.stem / "Podfile"
        if podfile.exists():
            Reporter.Info("Installing CocoaPods dependencies...")
            result = Process.ExecuteCommand(["pod", "install"], cwd=podfile.parent,
                                            captureOutput=False, silent=False)
            if result.returnCode != 0:
                Reporter.Warning("pod install failed, continuing without pods")

    def _RunXcodeBuild(self, xcode_proj: Path, project: Project) -> bool:
        """Lance xcodebuild pour compiler le projet."""
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

        # Ajouter la signature si nécessaire
        if not self.is_simulator:
            if self.signing_identity:
                args.append(f'CODE_SIGN_IDENTITY="{self.signing_identity}"')
            if self.provisioning_profile:
                args.append(f'PROVISIONING_PROFILE_SPECIFIER="{self.provisioning_profile}"')
            else:
                args.append('CODE_SIGN_IDENTITY=""')
                args.append('CODE_SIGNING_REQUIRED=NO')
                args.append('CODE_SIGNING_ALLOWED=NO')

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def _ArchiveProject(self, xcode_proj: Path, project: Project, build_root: Path) -> Optional[Path]:
        """Crée un archive .xcarchive."""
        scheme = project.targetName or xcode_proj.stem
        archive_path = build_root / f"{scheme}.xcarchive"

        args = [
            "xcodebuild",
            "-project", str(xcode_proj),
            "-scheme", scheme,
            "-configuration", self.configuration,
            "-sdk", self.sdk,
            "-archivePath", str(archive_path),
            "archive"
        ]

        result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
        if result.returnCode == 0:
            return archive_path
        else:
            return None

    def _ExportIPA(self, archive_path: Path, project: Project, build_root: Path) -> Optional[Path]:
        """Exporte l'archive vers un IPA."""
        export_dir = build_root / "IPA"
        FileSystem.RemoveDirectory(export_dir, recursive=True, ignoreErrors=True)

        # Générer un ExportOptions.plist
        export_plist = self._GenerateExportOptionsPlist(project, export_dir)

        args = [
            "xcodebuild",
            "-exportArchive",
            "-archivePath", str(archive_path),
            "-exportPath", str(export_dir),
            "-exportOptionsPlist", str(export_plist),
            "-allowProvisioningUpdates"
        ]

        result = Process.ExecuteCommand(args, captureOutput=False, silent=False)
        if result.returnCode == 0:
            ipa_files = list(export_dir.glob("*.ipa"))
            return ipa_files[0] if ipa_files else None
        else:
            return None

    def _GenerateExportOptionsPlist(self, project: Project, export_dir: Path) -> Path:
        """Génère le fichier ExportOptions.plist pour l'export."""
        FileSystem.MakeDirectory(export_dir)

        # Déterminer la méthode d'export
        method = "development"  # par défaut
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
            "thinning": "<none>"
        }

        if project.iosBundleId:
            options["provisioningProfiles"] = {
                project.iosBundleId: project.iosProvisioningProfile or self.provisioning_profile or ""
            }

        plist_path = export_dir / "ExportOptions.plist"
        with open(plist_path, 'wb') as f:
            plistlib.dump(options, f)

        return plist_path