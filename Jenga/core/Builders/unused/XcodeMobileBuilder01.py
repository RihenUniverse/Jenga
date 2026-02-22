import plistlib
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from Jenga.Core.Api import Project, ProjectKind, TargetOS
from ...Utils import Colored, FileSystem, Process, Reporter
from .AppleMobileBuilder import AppleMobileBuilder


class XcodeMobileBuilder(AppleMobileBuilder):
    """
    Builder Apple mobile utilisant xcodegen pour générer le projet Xcode,
    puis xcodebuild pour compiler. Affiche la progression en temps réel.
    """

    def __init__(self, workspace, config, platform, targetOs, targetArch, targetEnv=None, verbose=False):
        super().__init__(workspace, config, platform, targetOs, targetArch, targetEnv, verbose)
        self.configuration = self.config.capitalize() if self.config else "Debug"
        self.xcode_version = ""
        self.signing_identity: Optional[str] = None
        self.provisioning_profile: Optional[str] = None

        self._CheckXcode()
        self._CheckXcodeGen()

    def _CheckXcode(self) -> None:
        try:
            version = Process.Capture(["xcodebuild", "-version"])
            self.xcode_version = version.strip().split("\n")[0]
        except Exception as e:
            raise RuntimeError(f"Xcode is required for Apple mobile builds: {e}")

    def _CheckXcodeGen(self) -> None:
        """Vérifie que xcodegen est installé."""
        try:
            Process.Capture(["xcodegen", "--version"])
        except Exception:
            raise RuntimeError(
                "xcodegen not found. Please install it: `brew install xcodegen` or "
                "download from https://github.com/yonaskolb/XcodeGen"
            )

    # Ces méthodes ne sont pas utilisées directement car tout est géré par xcodebuild
    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"
        if project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        return ".app"

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        raise NotImplementedError("Direct compilation not used in Xcode mode")

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        return []

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        raise NotImplementedError("Direct linking not used in Xcode mode")

    def BuildProject(self, project: Project) -> bool:
        # Récupération de la version minimale
        self.min_version = self._GetMinimumVersion(project)

        # Récupération des infos de signature depuis le projet
        self.signing_identity = project.iosSigningIdentity
        self.provisioning_profile = project.iosProvisioningProfile

        Reporter.Info(f"Building {self.target_profile['display']} project {project.name} ({self.sdk_name})")

        # Répertoire de build
        build_root = Path(self.GetTargetDir(project)) / f"{self.target_profile['display'].lower()}-xcodebuild"
        FileSystem.MakeDirectory(build_root)

        # 1. Générer le projet Xcode avec xcodegen
        project_spec = self._GenerateXcodeGenSpec(project, build_root)
        spec_path = build_root / "project.yml"
        with open(spec_path, "w") as f:
            import yaml
            yaml.dump(project_spec, f, default_flow_style=False)

        # Exécuter xcodegen
        result = Process.ExecuteCommand(
            ["xcodegen", "--spec", str(spec_path)],
            cwd=build_root,
            captureOutput=False,
            silent=False
        )
        if result.returnCode != 0:
            Reporter.Error("xcodegen failed")
            return False

        # Trouver le projet généré (normalement project.xcodeproj dans build_root)
        xcode_proj = build_root / "project.xcodeproj"
        if not xcode_proj.exists():
            Reporter.Error("xcodegen did not generate project.xcodeproj")
            return False

        # 2. Installer CocoaPods si nécessaire
        self._InstallCocoaPodsIfNeeded(build_root)

        # 3. Lancer xcodebuild avec affichage en temps réel
        if not self._RunXcodeBuild(xcode_proj, project, build_root):
            return False

        # 4. Récupérer le chemin du .app généré
        app_bundle = self._FindAppBundle(build_root, project)
        if app_bundle:
            project._jengaLastAppBundle = str(app_bundle)
            Reporter.Success(f"App bundle generated: {app_bundle}")
        else:
            Reporter.Warning("App bundle not found, build may have failed")

        # 5. Archiver et exporter IPA si nécessaire (pour device)
        if not self.is_simulator:
            archive_path = self._ArchiveProject(xcode_proj, project, build_root)
            if archive_path:
                project._jengaLastArchivePath = str(archive_path)
                ipa_path = self._ExportIPA(archive_path, project, build_root)
                if ipa_path:
                    project._jengaLastIpaPath = str(ipa_path)
                    Reporter.Success(f"IPA generated: {ipa_path}")
                else:
                    Reporter.Warning("IPA export failed, archive created only.")
            else:
                Reporter.Warning("Archive creation failed.")

        return True

    def _GenerateXcodeGenSpec(self, project: Project, build_root: Path) -> dict:
        """Génère le dictionnaire de spécification pour xcodegen."""
        # Nom du projet
        proj_name = project.targetName or project.name

        # Déterminer le type de produit
        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            product_type = "application"
        elif project.kind == ProjectKind.STATIC_LIB:
            product_type = "static-library"
        elif project.kind == ProjectKind.SHARED_LIB:
            product_type = "dynamic-library"
        else:
            product_type = "application"

        # Plateforme supportée
        platform_name = self.target_profile["sdk_device"] if not self.is_simulator else self.target_profile["sdk_simulator"]

        # Sources : tous les fichiers listés dans project.files
        # On les copie d'abord dans un répertoire source (pour que xcodegen les trouve)
        src_dir = build_root / proj_name
        FileSystem.MakeDirectory(src_dir)
        base_dir = Path(project.location) if project.location else Path.cwd()
        for pattern in project.files:
            for f in FileSystem.ListFiles(base_dir, pattern, recursive=True, fullPath=True):
                src = Path(f)
                rel = src.relative_to(base_dir)
                dest = src_dir / rel
                FileSystem.MakeDirectory(dest.parent)
                shutil.copy2(src, dest)

        # Configuration de base
        spec = {
            "name": proj_name,
            "options": {
                "bundleIdPrefix": project.iosBundleId or f"com.{project.name}",
                "deploymentTarget": {
                    platform_name: self.min_version,
                },
            },
            "targets": {
                proj_name: {
                    "type": product_type,
                    "platform": platform_name,
                    "sources": [{"path": proj_name}],
                    "settings": {
                        "base": self._GetXcodeBuildSettings(project),
                    },
                }
            },
        }

        # Ajouter les frameworks
        frameworks = []
        for fw in self.target_profile.get("frameworks", []):
            frameworks.append(fw)
        if not self.is_simulator:
            for fw in self.target_profile.get("device_frameworks", []):
                frameworks.append(fw)
        for fw in project.frameworks:
            frameworks.append(fw)
        if frameworks:
            spec["targets"][proj_name]["settings"]["base"]["FRAMEWORK_SEARCH_PATHS"] = ["$(inherited)"]
            spec["targets"][proj_name]["dependencies"] = [
                {"framework": fw, "embed": False} for fw in frameworks
            ]

        # Bibliothèques (links)
        libs = []
        for lib in project.links:
            if lib.startswith("lib"):
                libs.append(lib[3:])  # enlever "lib"
            else:
                libs.append(lib)
        if libs:
            spec["targets"][proj_name]["settings"]["base"]["OTHER_LDFLAGS"] = [f"-l{lib}" for lib in libs]

        return spec

    def _GetXcodeBuildSettings(self, project: Project) -> dict:
        """Génère les paramètres de build pour Xcode."""
        settings = {
            "PRODUCT_NAME": project.targetName or project.name,
            "INFOPLIST_FILE": "Info.plist",  # sera créé par le builder ? À voir
            "CODE_SIGN_STYLE": "Manual" if self.signing_identity else "Automatic",
        }
        if self.signing_identity:
            settings["DEVELOPMENT_TEAM"] = project.iosTeamId or ""
            settings["PROVISIONING_PROFILE_SPECIFIER"] = self.provisioning_profile or ""
        # Définitions du préprocesseur
        defines = list(project.defines)
        if defines:
            settings["GCC_PREPROCESSOR_DEFINITIONS"] = defines
        # Optimisation
        opt = project.optimize.value if hasattr(project.optimize, "value") else project.optimize
        if opt == "Size":
            settings["GCC_OPTIMIZATION_LEVEL"] = "s"
        elif opt == "Speed":
            settings["GCC_OPTIMIZATION_LEVEL"] = "3"
        elif opt == "Full":
            settings["GCC_OPTIMIZATION_LEVEL"] = "fast"
        else:
            settings["GCC_OPTIMIZATION_LEVEL"] = "0"
        # Debug / Release
        if self.configuration == "Debug":
            settings["DEBUG_INFORMATION_FORMAT"] = "dwarf-with-dsym"
            settings["ENABLE_NS_ASSERTIONS"] = "YES"
        else:
            settings["DEBUG_INFORMATION_FORMAT"] = "dwarf"
            settings["ENABLE_NS_ASSERTIONS"] = "NO"
        # Flags supplémentaires
        if project.cflags or project.cxxflags:
            settings["OTHER_CFLAGS"] = project.cflags + project.cxxflags
        if project.ldflags:
            settings["OTHER_LDFLAGS"] = project.ldflags
        return settings

    def _InstallCocoaPodsIfNeeded(self, build_root: Path) -> None:
        """Installe les pods si un Podfile est présent."""
        podfile = build_root / "Podfile"
        if not podfile.exists():
            return
        Reporter.Info("Installing CocoaPods dependencies...")
        result = Process.ExecuteCommand(
            ["pod", "install"],
            cwd=build_root,
            captureOutput=False,
            silent=False
        )
        if result.returnCode != 0:
            Reporter.Warning("pod install failed, continuing without pods.")

    def _RunXcodeBuild(self, xcode_proj: Path, project: Project, build_root: Path) -> bool:
        """Lance xcodebuild et affiche la sortie en temps réel."""
        scheme = project.targetName or xcode_proj.stem
        derived_data = build_root / "DerivedData"

        args = [
            "xcodebuild",
            "-project", str(xcode_proj),
            "-scheme", scheme,
            "-configuration", self.configuration,
            "-sdk", self.sdk_name,
            "CONFIGURATION_BUILD_DIR=" + str(build_root / "build"),
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
                args.append("CODE_SIGN_IDENTITY=")
                args.append("CODE_SIGNING_REQUIRED=NO")
                args.append("CODE_SIGNING_ALLOWED=NO")

        # Exécuter avec pipe pour affichage en temps réel
        # On utilise subprocess.Popen et on lit ligne par ligne
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in process.stdout:
            print(line, end='')  # Afficher la ligne
        process.wait()
        self._lastResult = process
        return process.returncode == 0

    def _FindAppBundle(self, build_root: Path, project: Project) -> Optional[Path]:
        """Recherche le .app généré dans build_root/build."""
        build_dir = build_root / "build"
        pattern = f"{project.targetName or project.name}.app"
        for item in build_dir.iterdir():
            if item.name == pattern and item.is_dir():
                return item
        return None

    def _ArchiveProject(self, xcode_proj: Path, project: Project, build_root: Path) -> Optional[Path]:
        """Crée un archive .xcarchive."""
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
        """Exporte un .ipa depuis l'archive."""
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
        """Génère le fichier ExportOptions.plist."""
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
            "signingStyle": "manual" if self.signing_identity else "automatic",
            "stripSwiftSymbols": True,
            "compileBitcode": False,
            "thinning": "<none>",
        }
        if project.iosBundleId:
            options["provisioningProfiles"] = {
                project.iosBundleId: self.provisioning_profile or ""
            }
        plist_path = export_dir / "ExportOptions.plist"
        with open(plist_path, "wb") as f:
            plistlib.dump(options, f)
        return plist_path