import os
import shutil
import plistlib
import tempfile
from pathlib import Path
from typing import List, Optional

from Jenga.Core.Api import Project, ProjectKind, TargetOS
from ...Utils import Colored, FileSystem, Process, Reporter
from .AppleMobileBuilder import AppleMobileBuilder


class XcrunMobileBuilder(AppleMobileBuilder):
    """
    Builder Apple mobile utilisant xcrun (clang/clang++) directement.
    Produit un bundle .app signé (ou non) et éventuellement un .ipa.
    """

    def GetObjectExtension(self) -> str:
        return ".o"

    def GetOutputExtension(self, project: Project) -> str:
        if project.kind == ProjectKind.SHARED_LIB:
            return ".dylib"
        elif project.kind == ProjectKind.STATIC_LIB:
            return ".a"
        elif project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            return ""  # exécutable Unix
        else:
            return ""

    def GetModuleFlags(self, project: Project, sourceFile: str) -> List[str]:
        if not self.IsModuleFile(sourceFile):
            return []
        return [
            "-fmodules",
            "-fcxx-modules",
            "-fbuiltin-module-map",
            *self._GetTargetFlags(),
        ]

    def Compile(self, project: Project, sourceFile: str, objectFile: str) -> bool:
        src = Path(sourceFile)
        obj = Path(objectFile)
        FileSystem.MakeDirectory(obj.parent)

        compiler = self.toolchain.cxxPath if project.language.value in ("C++", "Objective-C++") else self.toolchain.ccPath
        args = [
            compiler,
            "-c",
            "-o", str(obj),
            *self.GetDependencyFlags(str(obj)),
            *self._GetTargetFlags(),
            "-arch", self._GetArchName(),
        ]
        args.extend(self._GetCommonCompilerFlags(project))
        if self.IsModuleFile(sourceFile):
            args.extend(self.GetModuleFlags(project, sourceFile))
        args.append(str(src))

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    def Link(self, project: Project, objectFiles: List[str], outputFile: str) -> bool:
        out = Path(outputFile)
        FileSystem.MakeDirectory(out.parent)

        if project.kind == ProjectKind.STATIC_LIB:
            # Utilisation de libtool ou ar
            ar = self.toolchain.arPath or "ar"
            args = [ar, "rcs", str(out)] + objectFiles
            result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
            self._lastResult = result
            return result.returnCode == 0

        # Pour les exécutables et libs partagées
        linker = self.toolchain.cxxPath
        args = [
            linker,
            "-o", str(out),
            *self._GetTargetFlags(),
            "-arch", self._GetArchName(),
        ]

        # Type de sortie
        if project.kind == ProjectKind.SHARED_LIB:
            args.append("-dynamiclib")

        # Frameworks
        args.extend(self._GetFrameworkLinkerArgs(project))

        # Bibliothèques
        args.extend(self._GetLibraryLinkerArgs(project))

        # Flags du linker
        args.extend(getattr(self.toolchain, "ldflags", []))
        args.extend(project.ldflags)

        # RPath pour exécutables (dans le bundle)
        if project.kind in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            args.append("-Wl,-rpath,@executable_path/Frameworks")

        # Objets
        args.extend(objectFiles)

        result = Process.ExecuteCommand(args, captureOutput=True, silent=False)
        self._lastResult = result
        return result.returnCode == 0

    # -----------------------------------------------------------------------
    # Construction du bundle .app
    # -----------------------------------------------------------------------

    def BuildProject(self, project: Project) -> bool:
        # Récupération de la version minimale AVANT la compilation
        self.min_version = self._GetMinimumVersion(project)

        # Appel à la méthode parente qui compile et lie
        if not super().BuildProject(project):
            return False

        # Si ce n'est pas une application, on s'arrête là
        if project.kind not in (ProjectKind.CONSOLE_APP, ProjectKind.WINDOWED_APP, ProjectKind.TEST_SUITE):
            return True

        # Récupération de la version minimale (déjà définie dans super().BuildProject)
        # self.min_version est déjà positionné

        # Construction du bundle
        return self._BuildAppBundle(project)

    def _BuildAppBundle(self, project: Project) -> bool:
        """Crée le bundle .app, signe et éventuellement génère un .ipa."""
        # Déterminer le nom de l'application
        app_name = project.targetName or project.name
        target_dir = Path(self.GetTargetDir(project))
        bundle_dir = target_dir / f"{app_name}.app"

        # Nettoyer l'ancien bundle
        FileSystem.RemoveDirectory(bundle_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(bundle_dir)

        # 1. Copier l'exécutable
        exe_path = self.GetTargetPath(project)
        if not exe_path.exists():
            Reporter.Error(f"Executable not found: {exe_path}")
            return False
        shutil.copy2(exe_path, bundle_dir / app_name)

        # 2. Générer Info.plist
        info_plist = self._GenerateInfoPlist(project)
        with open(bundle_dir / "Info.plist", "wb") as f:
            plistlib.dump(info_plist, f)

        # 3. Copier les ressources (embedResources)
        for pattern in project.embedResources:
            resolved = self.ResolveProjectPath(project, pattern)
            src = Path(resolved)
            if src.is_dir():
                dest = bundle_dir / src.name
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, bundle_dir / src.name)
                
        for pattern in project.iosResources:
            resolved = self.ResolveProjectPath(project, pattern)
            src = Path(resolved)
            if src.is_dir():
                dest = bundle_dir / src.name
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, bundle_dir / src.name)

        # 4. Copier les frameworks éventuels (dans le répertoire Frameworks)
        #    Les frameworks peuvent être spécifiés dans project.links avec un chemin direct
        frameworks_dir = bundle_dir / "Frameworks"
        FileSystem.MakeDirectory(frameworks_dir)
        for lib in project.links:
            if lib.endswith(".framework") and Path(lib).exists():
                shutil.copytree(lib, frameworks_dir / Path(lib).name, dirs_exist_ok=True)

        # 5. Signer le bundle si nécessaire
        if not self.is_simulator and project.iosSigningIdentity:
            if not self._SignBundle(project, bundle_dir):
                return False

        # 6. Générer un .ipa si demandé (ou si distribution)
        if not self.is_simulator and project.iosDistributionType != "development":
            ipa_path = self._GenerateIPA(project, bundle_dir)
            if ipa_path:
                Reporter.Success(f"IPA generated: {ipa_path}")
            else:
                Reporter.Warning("IPA generation failed, but .app was created.")

        Reporter.Success(f"App bundle created: {bundle_dir}")
        return True

    def _GenerateInfoPlist(self, project: Project) -> dict:
        """Génère le dictionnaire Info.plist à partir des propriétés du projet."""
        bundle_id = project.iosBundleId or f"com.{project.name}.app"
        platform_name = (
            str(self.target_profile["platform_simulator"])
            if self.is_simulator else str(self.target_profile["platform_device"])
        )
        plist = {
            "CFBundleDevelopmentRegion": "$(DEVELOPMENT_LANGUAGE)",
            "CFBundleExecutable": project.targetName or project.name,
            "CFBundleIdentifier": bundle_id,
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundleName": project.targetName or project.name,
            "CFBundlePackageType": "APPL",
            "CFBundleShortVersionString": project.iosVersion or "1.0",
            "CFBundleVersion": project.iosBuildNumber or "1",
            "CFBundleSupportedPlatforms": [platform_name],
            "UIDeviceFamily": list(self.target_profile["device_family"]),
            "MinimumOSVersion": self.min_version,
        }
        if bool(self.target_profile.get("requires_iphone_os", False)):
            plist["LSRequiresIPhoneOS"] = True
        if self.targetOs == TargetOS.IOS:
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
        # Pour tvOS/watchOS/visionOS, on pourrait ajouter des clés spécifiques
        # mais ce n'est pas obligatoire.
        return plist

    def _SignBundle(self, project: Project, bundle_dir: Path) -> bool:
        """Signe le bundle avec codesign."""
        identity = project.iosSigningIdentity
        entitlements = project.iosEntitlements
        if not identity:
            Reporter.Error("No signing identity provided for device build.")
            return False

        # Si un fichier entitlements est fourni, l'utiliser
        entitlements_arg = []
        if entitlements:
            ent_path = Path(self.ResolveProjectPath(project, entitlements))
            if ent_path.exists():
                entitlements_arg = ["--entitlements", str(ent_path)]
            else:
                Reporter.Warning(f"Entitlements file not found: {ent_path}")

        # Signer le bundle
        cmd = [
            "codesign",
            "--force",
            "--sign", identity,
            *entitlements_arg,
            str(bundle_dir)
        ]
        result = Process.ExecuteCommand(cmd, captureOutput=False, silent=False)
        if result.returnCode != 0:
            Reporter.Error("Code signing failed")
            return False

        # Vérifier la signature
        verify_cmd = ["codesign", "--verify", "--verbose", str(bundle_dir)]
        verify_result = Process.ExecuteCommand(verify_cmd, captureOutput=True, silent=True)
        if verify_result.returnCode != 0:
            Reporter.Warning("Code signing verification failed")
            # On ne bloque pas le build pour autant
        return True

    def _GenerateIPA(self, project: Project, bundle_dir: Path) -> Optional[Path]:
        """Crée un fichier .ipa à partir du bundle signé."""
        # Le .ipa est simplement un zip renommé du contenu du bundle dans Payload/
        target_dir = Path(self.GetTargetDir(project))
        ipa_path = target_dir / f"{project.targetName or project.name}.ipa"
        payload_dir = target_dir / "Payload"
        FileSystem.RemoveDirectory(payload_dir, recursive=True, ignoreErrors=True)
        FileSystem.MakeDirectory(payload_dir)
        shutil.copytree(bundle_dir, payload_dir / bundle_dir.name)

        # Créer le zip
        shutil.make_archive(str(ipa_path.with_suffix("")), 'zip', target_dir, "Payload")
        os.rename(str(ipa_path.with_suffix(".zip")), str(ipa_path))

        # Nettoyer
        FileSystem.RemoveDirectory(payload_dir, recursive=True, ignoreErrors=True)
        return ipa_path if ipa_path.exists() else None