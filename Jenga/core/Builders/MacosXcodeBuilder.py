import plistlib
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from Jenga.Core.Api import Project, ProjectKind, TargetOS, TargetArch
from ...Utils import Colored, FileSystem, Process, Reporter
from .AppleMobileBuilder import AppleMobileBuilder


class XcodeMobileBuilder(AppleMobileBuilder):
    """
    Builder Apple mobile utilisant xcodebuild via un projet Xcode généré.
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)
        self.configuration = self.config.capitalize() if self.config else "Debug"
        self.xcode_version = ""
        self.signing_identity: Optional[str] = None
        self.provisioning_profile: Optional[str] = None

        self._CheckXcode()
        self._ResolveSigningIdentity(workspace)

    def _CheckXcode(self) -> None:
        try:
            version = Process.Capture(["xcodebuild", "-version"])
            if not version:
                raise RuntimeError("xcodebuild not found")
            self.xcode_version = version.strip().split("\n")[0]
        except Exception as e:
            raise RuntimeError(f"Xcode is required for Apple mobile builds: {e}")

    def _ResolveSigningIdentity(self, workspace) -> None:
        # Sera surchargée par les valeurs du projet dans BuildProject
        self.signing_identity = None
        self.provisioning_profile = None

    def GetObjectExtension(self) -> str:
        return ".o"  # non utilisé en mode Xcode

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"
        if project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        return ".app"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        # Non utilisé en mode Xcode (tout est géré par xcodebuild)
        raise NotImplementedError("Direct compilation not used in Xcode mode")

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        # Non utilisé
        return []

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        # Non utilisé
        raise NotImplementedError("Direct linking not used in Xcode mode")

    def BuildProject(self, project: Project) -> bool:
        # Récupération de la version minimale avant toute chose
        self.min_version = self._GetMinimumVersion(project)

        # Récupération des infos de signature depuis le projet
        self.signing_identity = project.iosSigningIdentity
        self.provisioning_profile = project.iosProvisioningProfile

        Reporter.Info(f"Building {self.target_profile['display']} project {project.name} ({self.sdk_name})")

        project._jengaLastArchivePath = ""
        project._jengaLastIpaPath = ""

        build_root = Path(self.GetTargetDir(project)) / f"{self.target_profile['display'].lower()}-build"
        FileSystem.MakeDirectory(build_root)

        # Génération du projet Xcode
        xcode_proj = XcodeProjectGenerator.Generate(
            project=project,
            target_os=self.targetOs,
            target_arch=self.targetArch,
            is_simulator=self.is_simulator,
            build_dir=build_root,
            target_profile=self.target_profile,
            min_version=self.min_version,
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
            "-sdk", self.sdk_name,
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
            "-sdk", self.sdk_name,
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
    

import plistlib
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from Jenga.Core.Api import Project, ProjectKind, TargetOS
from ...Utils import FileSystem


class XcodeProjectGenerator:
    """Génère un projet Xcode minimal à partir d'un projet Jenga."""

    @staticmethod
    def Generate(
        project: Project,
        target_os: TargetOS,
        target_arch: TargetArch,
        is_simulator: bool,
        build_dir: Path,
        target_profile: Dict[str, object],
        min_version: str,
    ) -> Optional[Path]:
        proj_name = project.targetName or project.name
        proj_dir = build_dir / f"{proj_name}.xcodeproj"
        FileSystem.RemoveDirectory(proj_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(proj_dir)

        XcodeProjectGenerator._WritePbxproj(
            project, target_os, target_arch, is_simulator,
            proj_dir, target_profile, min_version
        )
        XcodeProjectGenerator._WriteScheme(project, proj_name, proj_dir)
        XcodeProjectGenerator._WriteWorkspaceSettings(proj_dir)

        src_dir = proj_dir.parent / proj_name
        FileSystem.MakeDirectory(src_dir)
        XcodeProjectGenerator._CopySourceFiles(project, src_dir)

        info_plist = XcodeProjectGenerator._GenerateInfoPlist(
            project, target_os, is_simulator, src_dir, target_profile, min_version
        )
        if not info_plist:
            return None

        if project.links or project.frameworks:
            XcodeProjectGenerator._GeneratePodfile(
                project, src_dir, str(target_profile.get("cocoapods_platform", "ios"))
            )
        return proj_dir

    # -----------------------------------------------------------------------
    # Écriture du fichier project.pbxproj
    # -----------------------------------------------------------------------

    @staticmethod
    def _WritePbxproj(
        project: Project,
        target_os: TargetOS,
        target_arch: TargetArch,
        is_simulator: bool,
        proj_dir: Path,
        target_profile: Dict[str, object],
        min_version: str,
    ) -> None:
        """Génère le fichier project.pbxproj au format XML."""
        proj_id = uuid.uuid4().hex.upper()[:24]
        target_id = uuid.uuid4().hex.upper()[:24]
        build_conf_list_id = uuid.uuid4().hex.upper()[:24]
        main_group_id = uuid.uuid4().hex.upper()[:24]
        product_group_id = uuid.uuid4().hex.upper()[:24]

        # Déterminer le type de produit
        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            product_type = "com.apple.product-type.application"
            product_ext = "app"
        elif project.kind == ProjectKind.STATIC_LIB:
            product_type = "com.apple.product-type.library.static"
            product_ext = "a"
        elif project.kind == ProjectKind.SHARED_LIB:
            product_type = "com.apple.product-type.library.dynamic"
            product_ext = "dylib"
        else:
            product_type = "com.apple.product-type.application"
            product_ext = "app"

        # Nom du produit
        product_name = project.targetName or project.name

        # Création des références de fichiers pour les sources
        src_dir = proj_dir.parent / product_name
        file_refs = XcodeProjectGenerator._CollectFileReferences(src_dir, project)

        # Construction du dictionnaire pbxproj
        pbxproj = {
            "archiveVersion": "1",
            "classes": {},
            "objectVersion": "56",  # Xcode 14+
            "objects": {
                proj_id: {
                    "isa": "PBXProject",
                    "attributes": {
                        "LastUpgradeCheck": "1500",  # Xcode 15.0
                        "TargetAttributes": {
                            target_id: {
                                "CreatedOnToolsVersion": "15.0"
                            }
                        }
                    },
                    "buildConfigurationList": build_conf_list_id,
                    "compatibilityVersion": "Xcode 14.0",
                    "developmentRegion": "en",
                    "hasScannedForEncodings": "0",
                    "knownRegions": ["en", "Base"],
                    "mainGroup": main_group_id,
                    "productRefGroup": product_group_id,
                    "projectDirPath": "",
                    "projectRoot": "",
                    "targets": [target_id],
                },
                target_id: {
                    "isa": "PBXNativeTarget",
                    "buildConfigurationList": XcodeProjectGenerator._GetBuildConfigurationList(
                        project, target_profile, min_version, is_simulator
                    ),
                    "buildPhases": XcodeProjectGenerator._GetBuildPhases(project),
                    "buildRules": [],
                    "dependencies": [],
                    "name": product_name,
                    "productName": product_name,
                    "productReference": XcodeProjectGenerator._GetProductReference(product_name, product_ext),
                    "productType": product_type,
                },
                build_conf_list_id: {
                    "isa": "XCConfigurationList",
                    "buildConfigurations": XcodeProjectGenerator._GetBuildConfigurations(
                        project, target_profile, min_version, is_simulator
                    ),
                    "defaultConfigurationIsVisible": "0",
                    "defaultConfigurationName": "Debug",
                },
                main_group_id: {
                    "isa": "PBXGroup",
                    "children": [
                        product_group_id,
                        XcodeProjectGenerator._GetSourceGroup(src_dir, file_refs),
                    ],
                    "sourceTree": "<group>",
                    "name": product_name,
                },
                product_group_id: {
                    "isa": "PBXGroup",
                    "children": [
                        XcodeProjectGenerator._GetProductFileRef(product_name, product_ext)
                    ],
                    "name": "Products",
                    "sourceTree": "<group>",
                },
                **file_refs,  # injecter toutes les références de fichiers
            },
            "rootObject": proj_id,
        }

        # Écrire le fichier
        proj_path = proj_dir / "project.pbxproj"
        with open(proj_path, "wb") as f:
            plistlib.dump(pbxproj, f, fmt=plistlib.FMT_XML)

    @staticmethod
    def _GetBuildConfigurationList(
        project: Project,
        target_profile: Dict[str, object],
        min_version: str,
        is_simulator: bool
    ) -> Dict:
        """Retourne la liste de configurations de build."""
        return {
            "isa": "XCConfigurationList",
            "buildConfigurations": [
                XcodeProjectGenerator._GetBuildConfiguration(
                    "Debug", project, target_profile, min_version, is_simulator
                ),
                XcodeProjectGenerator._GetBuildConfiguration(
                    "Release", project, target_profile, min_version, is_simulator
                ),
            ],
            "defaultConfigurationIsVisible": "0",
            "defaultConfigurationName": "Debug",
        }

    @staticmethod
    def _GetBuildConfigurations(
        project: Project,
        target_profile: Dict[str, object],
        min_version: str,
        is_simulator: bool
    ) -> List[Dict]:
        """Retourne les deux configurations (Debug, Release)."""
        debug_id = uuid.uuid4().hex.upper()[:24]
        release_id = uuid.uuid4().hex.upper()[:24]
        debug = {
            "isa": "XCBuildConfiguration",
            "name": "Debug",
            "buildSettings": XcodeProjectGenerator._GetBuildSettings(
                "Debug", project, target_profile, min_version, is_simulator
            ),
        }
        release = {
            "isa": "XCBuildConfiguration",
            "name": "Release",
            "buildSettings": XcodeProjectGenerator._GetBuildSettings(
                "Release", project, target_profile, min_version, is_simulator
            ),
        }
        return [debug, release]

    @staticmethod
    def _GetBuildSettings(
        config: str,
        project: Project,
        target_profile: Dict[str, object],
        min_version: str,
        is_simulator: bool
    ) -> Dict:
        """Génère les paramètres de build pour une configuration donnée."""
        # Clé de déploiement selon la plateforme
        deployment_key = str(target_profile.get("deployment_key", "IPHONEOS_DEPLOYMENT_TARGET"))

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
            "GCC_WARN_ABOUT_RETURN_TYPE": "YES",
            "GCC_WARN_UNUSED_VARIABLE": "YES",
            "MTL_ENABLE_DEBUG_INFO": "INCLUDE_SOURCE" if config == "Debug" else "NO",
            "MTL_FAST_MATH": "YES",
            "PRODUCT_NAME": project.targetName or project.name,
            "SDKROOT": str(target_profile["sdk_device"] if not is_simulator else target_profile["sdk_simulator"]),
            "TARGETED_DEVICE_FAMILY": str(target_profile.get("device_family_setting", "1,2")),
            deployment_key: min_version,
        }

        # Définitions du préprocesseur
        defines = list(project.defines)
        if config == "Debug":
            defines.append("DEBUG=1")
        if defines:
            settings["GCC_PREPROCESSOR_DEFINITIONS"] = defines + ["$(inherited)"]

        # Optimisation
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

        # Flags de l'éditeur de liens (frameworks + bibliothèques)
        ldflags = []
        # Frameworks
        for fw in project.frameworks:
            ldflags.extend(["-framework", fw])
        # Bibliothèques
        for lib in project.links:
            if XcodeProjectGenerator._IsDirectLibPath(lib):
                ldflags.append(lib)
            else:
                ldflags.append(f"-l{lib}")
        if ldflags:
            settings["OTHER_LDFLAGS"] = ldflags

        # Flags supplémentaires du projet
        if project.cflags or project.cxxflags:
            all_cflags = list(project.cflags) + list(project.cxxflags)
            settings["OTHER_CFLAGS"] = all_cflags

        return settings

    @staticmethod
    def _IsDirectLibPath(lib: str) -> bool:
        p = Path(lib)
        return p.suffix in (".a", ".dylib", ".so", ".framework", ".lib") or "/" in lib or "\\" in lib or p.is_absolute()

    @staticmethod
    def _GetBuildPhases(project: Project) -> List[Dict]:
        """Retourne les phases de build (sources, frameworks, ressources)."""
        phases = []
        # Phase de compilation des sources
        phases.append({
            "isa": "PBXSourcesBuildPhase",
            "buildActionMask": "2147483647",
            "files": [],  # sera rempli par Xcode automatiquement
            "runOnlyForDeploymentPostprocessing": "0",
        })
        # Phase de link des frameworks
        phases.append({
            "isa": "PBXFrameworksBuildPhase",
            "buildActionMask": "2147483647",
            "files": [],
            "runOnlyForDeploymentPostprocessing": "0",
        })
        # Phase des ressources
        if project.embedResources:
            phases.append({
                "isa": "PBXResourcesBuildPhase",
                "buildActionMask": "2147483647",
                "files": [],
                "runOnlyForDeploymentPostprocessing": "0",
            })
        return phases

    @staticmethod
    def _GetProductReference(name: str, ext: str) -> Dict:
        return {
            "isa": "PBXFileReference",
            "lastKnownFileType": "wrapper.application" if ext == "app" else "archive.ar" if ext == "a" else "compiled.mach-o.dylib",
            "name": f"{name}.{ext}",
            "path": f"{name}.{ext}",
            "sourceTree": "BUILT_PRODUCTS_DIR",
        }

    @staticmethod
    def _GetSourceGroup(src_dir: Path, file_refs: Dict) -> Dict:
        """Retourne le groupe principal des sources."""
        group_id = uuid.uuid4().hex.upper()[:24]
        children = []
        for ref_id, ref_data in file_refs.items():
            if ref_data.get("isa") == "PBXFileReference":
                children.append(ref_id)
        return {
            "isa": "PBXGroup",
            "children": children,
            "name": src_dir.name,
            "sourceTree": "<group>",
            "path": src_dir.name,
        }

    @staticmethod
    def _GetProductFileRef(name: str, ext: str) -> Dict:
        ref_id = uuid.uuid4().hex.upper()[:24]
        return {
            ref_id: {
                "isa": "PBXFileReference",
                "lastKnownFileType": "wrapper.application" if ext == "app" else "archive.ar" if ext == "a" else "compiled.mach-o.dylib",
                "name": f"{name}.{ext}",
                "path": f"{name}.{ext}",
                "sourceTree": "BUILT_PRODUCTS_DIR",
            }
        }

    @staticmethod
    def _CollectFileReferences(src_dir: Path, project: Project) -> Dict:
        """Collecte toutes les références de fichiers sources."""
        refs = {}
        base_dir = Path(project.location) if project.location else Path.cwd()
        for pattern in project.files:
            for f in FileSystem.ListFiles(base_dir, pattern, recursive=True, fullPath=True):
                rel_path = Path(f).relative_to(base_dir)
                dest_path = src_dir / rel_path
                # Le fichier a déjà été copié par _CopySourceFiles
                # On crée une référence avec un ID unique
                ref_id = uuid.uuid4().hex.upper()[:24]
                # Déterminer le type de fichier
                ext = dest_path.suffix.lower()
                if ext in (".c", ".cpp", ".cc", ".cxx", ".m", ".mm", ".h", ".hpp"):
                    file_type = "sourcecode.c.objc" if ext in (".m", ".mm") else "sourcecode.cpp.cpp"
                else:
                    file_type = "file"
                refs[ref_id] = {
                    "isa": "PBXFileReference",
                    "lastKnownFileType": file_type,
                    "name": dest_path.name,
                    "path": str(rel_path),
                    "sourceTree": "<group>",
                }
        return refs

    # -----------------------------------------------------------------------
    # Écriture du schéma
    # -----------------------------------------------------------------------

    @staticmethod
    def _WriteScheme(project: Project, proj_name: str, proj_dir: Path) -> None:
        """Génère le fichier .xcscheme."""
        scheme_dir = proj_dir / "xcshareddata" / "xcschemes"
        FileSystem.MakeDirectory(scheme_dir)
        scheme_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion = "1500" version = "1.7">
  <BuildAction parallelizeBuildables = "YES" buildImplicitDependencies = "YES">
    <BuildActionEntries>
      <BuildActionEntry buildForTesting = "YES" buildForRunning = "YES" buildForProfiling = "YES" buildForArchiving = "YES" buildForAnalyzing = "YES">
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
  <TestAction buildConfiguration = "Debug" selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv = "YES">
    <Testables>
    </Testables>
  </TestAction>
  <LaunchAction buildConfiguration = "Debug" selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB" launchStyle = "0" useCustomWorkingDirectory = "NO" ignoresPersistentStateOnLaunch = "NO" debugDocumentVersioning = "YES" debugServiceExtension = "internal" allowLocationSimulation = "YES">
    <BuildableProductRunnable runnableDebuggingMode = "0">
      <BuildableReference
          BuildableIdentifier = "primary"
          BlueprintIdentifier = "{proj_name}"
          BuildableName = "{project.targetName or proj_name}.app"
          BlueprintName = "{project.targetName or proj_name}"
          ReferencedContainer = "container:{proj_name}.xcodeproj">
      </BuildableReference>
    </BuildableProductRunnable>
  </LaunchAction>
  <ProfileAction buildConfiguration = "Release" shouldUseLaunchSchemeArgsEnv = "YES" savedToolIdentifier = "" useCustomWorkingDirectory = "NO" debugDocumentVersioning = "YES">
    <BuildableProductRunnable runnableDebuggingMode = "0">
      <BuildableReference
          BuildableIdentifier = "primary"
          BlueprintIdentifier = "{proj_name}"
          BuildableName = "{project.targetName or proj_name}.app"
          BlueprintName = "{project.targetName or proj_name}"
          ReferencedContainer = "container:{proj_name}.xcodeproj">
      </BuildableReference>
    </BuildableProductRunnable>
  </ProfileAction>
  <AnalyzeAction buildConfiguration = "Debug">
  </AnalyzeAction>
  <ArchiveAction buildConfiguration = "Release" revealArchiveInOrganizer = "YES">
  </ArchiveAction>
</Scheme>
"""
        (scheme_dir / f"{proj_name}.xcscheme").write_text(scheme_content, encoding="utf-8")

    # -----------------------------------------------------------------------
    # Paramètres de l'espace de travail
    # -----------------------------------------------------------------------

    @staticmethod
    def _WriteWorkspaceSettings(proj_dir: Path) -> None:
        """Génère les paramètres de l'espace de travail."""
        settings_dir = proj_dir / "project.xcworkspace" / "xcshareddata"
        FileSystem.MakeDirectory(settings_dir)
        settings_path = settings_dir / "WorkspaceSettings.xcsettings"
        settings_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>BuildSystemType</key>
    <string>Original</string>
</dict>
</plist>
"""
        settings_path.write_text(settings_content, encoding="utf-8")

    # -----------------------------------------------------------------------
    # Copie des fichiers sources
    # -----------------------------------------------------------------------

    @staticmethod
    def _CopySourceFiles(project: Project, src_dir: Path) -> None:
        """Copie les fichiers sources dans le répertoire du projet."""
        base_dir = Path(project.location) if project.location else Path.cwd()
        for pattern in project.files:
            for f in FileSystem.ListFiles(base_dir, pattern, recursive=True, fullPath=True):
                src = Path(f)
                rel = src.relative_to(base_dir)
                dest = src_dir / rel
                FileSystem.MakeDirectory(dest.parent)
                shutil.copy2(src, dest)

    # -----------------------------------------------------------------------
    # Génération du Podfile pour CocoaPods
    # -----------------------------------------------------------------------

    @staticmethod
    def _GeneratePodfile(project: Project, src_dir: Path, platform_name: str) -> None:
        """Génère un Podfile si des dépendances CocoaPods sont détectées."""
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

    # -----------------------------------------------------------------------
    # Génération du Info.plist
    # -----------------------------------------------------------------------

    @staticmethod
    def _GenerateInfoPlist(
        project: Project,
        target_os: TargetOS,
        is_simulator: bool,
        src_dir: Path,
        target_profile: Dict[str, object],
        min_version: str,
    ) -> Optional[Path]:
        """Génère le fichier Info.plist pour l'application."""
        plist_path = src_dir / "Info.plist"
        bundle_id = project.iosBundleId or f"com.{project.name}.app"
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
            "UIDeviceFamily": list(target_profile["device_family"]),
            "MinimumOSVersion": min_version,
        }
        if bool(target_profile.get("requires_iphone_os", False)):
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
        # Pour tvOS/watchOS, on n'ajoute pas les orientations
        with open(plist_path, "wb") as f:
            plistlib.dump(plist, f)
        return plist_path