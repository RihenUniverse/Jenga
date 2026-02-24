#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package command – Crée des packages distribuables pour toutes les plateformes supportées.
- Android : APK, AAB (via AndroidBuilder)
- iOS : IPA (via IOSBuilder)
- Windows : MSI, EXE installer, ZIP (via WiX, InnoSetup, ou outils natifs)
- Linux : DEB, RPM, AppImage, Snap
- macOS : PKG, DMG
- Web : ZIP (via EmscriptenBuilder)
"""

import argparse
import sys
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict

from ..Utils import Colored, Display, FileSystem, Process
from ..Core.Loader import Loader
from ..Core.Cache import Cache
from ..Core.Builder import Builder
from ..Core import Api


class PackageCommand:
    """jenga package [--platform PLATFORM] [--config CONFIG] [--output DIR] [--project PROJECT] [--type TYPE]"""

    SUPPORTED_PLATFORMS = {
        'android': {'apk', 'aab'},
        'ios': {'ipa'},
        'tvos': {'ipa'},
        'watchos': {'ipa'},
        'windows': {'msi', 'exe', 'zip'},
        'linux': {'deb', 'rpm', 'appimage', 'snap'},
        'macos': {'pkg', 'dmg'},
        'web': {'zip'},
    }

    DEFAULT_PACKAGE_TYPE = {
        'android': 'apk',
        'ios': 'ipa',
        'tvos': 'ipa',
        'watchos': 'ipa',
        'windows': 'zip',
        'linux': 'deb',
        'macos': 'pkg',
        'web': 'zip',
    }

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(prog="jenga package", description="Create distributable packages.")
        parser.add_argument("--platform", required=True, choices=list(PackageCommand.SUPPORTED_PLATFORMS.keys()),
                            help="Target platform")
        parser.add_argument("--ios-builder", choices=["direct", "xcode", "xbuilder"], default=None,
                            help="Apple mobile builder backend (direct or xcode/xbuilder).")
        parser.add_argument("--config", default="Release", help="Build configuration (default: Release)")
        parser.add_argument("--output", "-o", default="./dist", help="Output directory (default: ./dist)")
        parser.add_argument("--project", help="Specific project to package (default: first executable)")
        parser.add_argument("--type", help="Package type (e.g., apk, aab, ipa, msi, deb). Default depends on platform.")
        parser.add_argument("--no-daemon", action="store_true", help="Do not use daemon")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--jenga-file", help="Path to the workspace .jenga file (default: auto-detected)")
        parsed = parser.parse_args(args)

        # Déterminer le répertoire de travail (workspace root)
        workspace_root = Path.cwd()
        if parsed.jenga_file:
            entry_file = Path(parsed.jenga_file).resolve()
            if not entry_file.exists():
                Colored.PrintError(f"Jenga file not found: {entry_file}")
                return 1
        else:
            entry_file = FileSystem.FindWorkspaceEntry(workspace_root)
            if not entry_file:
                Colored.PrintError("No .jenga workspace file found.")
                return 1
        workspace_root = entry_file.parent

        # Déterminer le type de package par défaut
        pkg_type = parsed.type
        if not pkg_type:
            pkg_type = PackageCommand.DEFAULT_PACKAGE_TYPE.get(parsed.platform)
            if not pkg_type:
                # Fallback de sûreté, stable.
                pkg_type = sorted(PackageCommand.SUPPORTED_PLATFORMS[parsed.platform])[0]

        if pkg_type not in PackageCommand.SUPPORTED_PLATFORMS[parsed.platform]:
            Colored.PrintError(f"Unsupported package type '{pkg_type}' for platform '{parsed.platform}'.")
            return 1

        # Charger le workspace (avec cache si possible)
        loader = Loader(verbose=parsed.verbose)
        cache = Cache(workspace_root, workspaceName=entry_file.stem)

        workspace = None
        if not parsed.no_daemon:
            from ..Core.Daemon import DaemonClient, DaemonStatus
            client = DaemonClient(workspace_root)
            if client.IsAvailable():
                Colored.PrintInfo("Using build daemon...")
                try:
                    response = client.SendCommand('package', {
                        'platform': parsed.platform,
                        'config': parsed.config,
                        'output': parsed.output,
                        'project': parsed.project,
                        'type': pkg_type,
                        'verbose': parsed.verbose
                    })
                    if response.get('status') == 'ok':
                        return response.get('return_code', 0)
                    else:
                        Colored.PrintError(f"Daemon package failed: {response.get('message')}")
                        return 1
                except Exception as e:
                    Colored.PrintWarning(f"Daemon error: {e}, falling back to direct package.")

        if workspace is None:
            workspace = cache.LoadWorkspace(entry_file, loader)
        if workspace is None:
            workspace = loader.LoadWorkspace(str(entry_file))
            if workspace:
                cache.SaveWorkspace(workspace, entry_file, loader)

        if workspace is None:
            Colored.PrintError("Failed to load workspace.")
            return 1

        # Sélectionner le projet à packager
        project_name = parsed.project
        if not project_name:
            # Chercher le startProject ou premier exécutable
            project_name = workspace.startProject
            if not project_name:
                for name, proj in workspace.projects.items():
                    if proj.kind in (Api.ProjectKind.CONSOLE_APP, Api.ProjectKind.WINDOWED_APP):
                        project_name = name
                        break
        if not project_name or project_name not in workspace.projects:
            Colored.PrintError(f"Project '{project_name}' not found.")
            return 1

        project = workspace.projects[project_name]

        # Créer le builder pour ce projet (nécessaire pour connaître les chemins de sortie)
        try:
            from ..Commands.build import BuildCommand
            builder = PackageCommand._CreateBuilder(
                workspace, parsed.config, parsed.platform, project_name, parsed.verbose,
                action="package",
                options=BuildCommand.CollectFilterOptions(
                    config=parsed.config,
                    platform=parsed.platform,
                    target=project_name,
                    verbose=parsed.verbose,
                    no_cache=False,
                    no_daemon=parsed.no_daemon,
                    extra=(
                        ["action:package", f"package:{pkg_type}"] +
                        ([f"ios-builder={parsed.ios_builder}"] if parsed.ios_builder else [])
                    )
                )
            )
        except Exception as e:
            Colored.PrintError(f"Cannot create builder: {e}")
            return 1

        output_dir = Path(parsed.output).resolve()
        FileSystem.MakeDirectory(output_dir)

        # Dispatch selon plateforme
        if parsed.platform == 'android':
            return PackageCommand._PackageAndroid(project, builder, pkg_type, output_dir)
        elif parsed.platform in ('ios', 'tvos', 'watchos'):
            return PackageCommand._PackageIOS(project, builder, pkg_type, output_dir)
        elif parsed.platform == 'windows':
            return PackageCommand._PackageWindows(project, builder, pkg_type, output_dir)
        elif parsed.platform == 'linux':
            return PackageCommand._PackageLinux(project, builder, pkg_type, output_dir)
        elif parsed.platform == 'macos':
            return PackageCommand._PackageMacOS(project, builder, pkg_type, output_dir)
        elif parsed.platform == 'web':
            return PackageCommand._PackageWeb(project, builder, pkg_type, output_dir)
        else:
            Colored.PrintError(f"Packaging for platform '{parsed.platform}' not implemented.")
            return 1

    @staticmethod
    def _CreateBuilder(workspace,
                       config: str,
                       platform: str,
                       target: str,
                       verbose: bool,
                       action: str = "package",
                       options: Optional[List[str]] = None) -> Builder:
        """Crée un builder pour le projet cible."""
        from ..Commands.build import BuildCommand
        return BuildCommand.CreateBuilder(
            workspace, config, platform, target, verbose,
            action=action,
            options=options
        )

    # -----------------------------------------------------------------------
    # Android
    # -----------------------------------------------------------------------

    @staticmethod
    def _PackageAndroid(project, builder, pkg_type: str, output_dir: Path) -> int:
        """APK / AAB packaging."""
        if not hasattr(builder, 'BuildAPK') or not hasattr(builder, 'BuildAAB'):
            Colored.PrintError("AndroidBuilder not available.")
            return 1

        # Construire les bibliothèques natives si nécessaire
        # Note: On suppose que le build a déjà été fait. Si ce n'est pas le cas, on peut appeler builder.BuildProject(project)
        if not builder.BuildProject(project):
            Colored.PrintError("Build failed, cannot package.")
            return 1

        # Récupérer les .so générés
        libs = []
        target_dir = builder.GetTargetDir(project)
        for so in target_dir.glob("*.so"):
            libs.append(str(so))

        if not libs:
            Colored.PrintError("No native libraries found.")
            return 1

        if pkg_type == 'apk':
            if not builder.BuildAPK(project, libs):
                return 1
            # Copier l'APK vers output_dir
            apk_path = builder.GetTargetDir(project) / f"{project.targetName or project.name}.apk"
            if apk_path.exists():
                shutil.copy2(apk_path, output_dir / apk_path.name)
                Colored.PrintSuccess(f"APK packaged: {output_dir / apk_path.name}")
                return 0
            return 1

        elif pkg_type == 'aab':
            if not hasattr(builder, 'BuildAAB'):
                Colored.PrintError("AAB packaging not supported by this builder.")
                return 1
            if not builder.BuildAAB(project, libs):
                return 1
            aab_path = builder.GetTargetDir(project) / f"{project.targetName or project.name}.aab"
            if aab_path.exists():
                shutil.copy2(aab_path, output_dir / aab_path.name)
                Colored.PrintSuccess(f"AAB packaged: {output_dir / aab_path.name}")
                return 0
            return 1

        return 1

    # -----------------------------------------------------------------------
    # iOS
    # -----------------------------------------------------------------------

    @staticmethod
    def _PackageIOS(project, builder, pkg_type: str, output_dir: Path) -> int:
        """IPA packaging."""
        if not hasattr(builder, 'ExportIPA'):
            Colored.PrintError("IOSBuilder does not support ExportIPA.")
            return 1

        # Build project
        if not builder.BuildProject(project):
            return 1

        # Localiser le bundle .app
        target_dir = builder.GetTargetDir(project)
        app_bundle = target_dir / f"{project.targetName or project.name}.app"
        if not app_bundle.exists():
            Colored.PrintError(f".app bundle not found: {app_bundle}")
            return 1

        # Exporter IPA
        ipa_path = builder.ExportIPA(app_bundle, project)
        if not ipa_path:
            return 1

        shutil.copy2(ipa_path, output_dir / ipa_path.name)
        Colored.PrintSuccess(f"IPA packaged: {output_dir / ipa_path.name}")
        return 0

    # -----------------------------------------------------------------------
    # Windows
    # -----------------------------------------------------------------------

    @staticmethod
    def _PackageWindows(project, builder, pkg_type: str, output_dir: Path) -> int:
        """Création d'installateur Windows."""
        # Build project
        if not builder.BuildProject(project):
            return 1

        exe_path = builder.GetTargetPath(project)
        if not exe_path.exists():
            Colored.PrintError(f"Executable not found: {exe_path}")
            return 1

        if pkg_type == 'zip':
            # Créer une archive ZIP
            import zipfile
            zip_path = output_dir / f"{project.targetName or project.name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(exe_path, exe_path.name)
                # Ajouter les DLLs dépendantes
                for dep in project.dependFiles:
                    dep_path = Path(dep)
                    if dep_path.exists():
                        zf.write(dep_path, dep_path.name)
            Colored.PrintSuccess(f"ZIP package: {zip_path}")
            return 0

        elif pkg_type == 'msi':
            # Utiliser WiX Toolset (candle + light)
            # Vérifier présence de wix
            if not FileSystem.FindExecutable("candle"):
                Colored.PrintError("WiX Toolset not found. Please install WiX.")
                return 1
            # Générer .wxs
            wxs_path = output_dir / f"{project.name}.wxs"
            PackageCommand._GenerateWiXTemplate(project, builder, exe_path, wxs_path)
            # Compiler
            obj_path = output_dir / f"{project.name}.wixobj"
            msi_path = output_dir / f"{project.name}.msi"
            if Process.Run(["candle", str(wxs_path), "-o", str(obj_path)]) != 0:
                return 1
            if Process.Run(["light", str(obj_path), "-o", str(msi_path)]) != 0:
                return 1
            Colored.PrintSuccess(f"MSI package: {msi_path}")
            return 0

        elif pkg_type == 'exe':
            # Utiliser Inno Setup
            if not FileSystem.FindExecutable("iscc"):
                Colored.PrintError("Inno Setup not found. Please install Inno Setup.")
                return 1
            iss_path = output_dir / f"{project.name}.iss"
            PackageCommand._GenerateInnoScript(project, builder, exe_path, iss_path)
            exe_installer = output_dir / f"{project.name}_setup.exe"
            if Process.Run(["iscc", str(iss_path), f"/O{output_dir}", f"/F{project.name}_setup"]) != 0:
                return 1
            Colored.PrintSuccess(f"EXE installer: {output_dir / f'{project.name}_setup.exe'}")
            return 0

        return 1

    @staticmethod
    def _GenerateWiXTemplate(project, builder, exe_path: Path, output: Path):
        """Génère un fichier .wxs pour WiX."""
        import xml.etree.ElementTree as ET
        root = ET.Element("Wix", xmlns="http://schemas.microsoft.com/wix/2006/wi")
        product = ET.SubElement(root, "Product",
                                Name=project.targetName or project.name,
                                Manufacturer="Jenga",
                                Id="*",
                                UpgradeCode="*",
                                Language="1033",
                                Codepage="1252",
                                Version="1.0.0")
        package = ET.SubElement(product, "Package",
                                InstallerVersion="200",
                                Compressed="yes",
                                InstallScope="perMachine")
        media = ET.SubElement(product, "Media", Id="1", Cabinet="setup.cab", EmbedCab="yes")
        directory = ET.SubElement(product, "Directory", Id="TARGETDIR", Name="SourceDir")
        prog_files = ET.SubElement(directory, "Directory", Id="ProgramFiles64Folder")
        app_dir = ET.SubElement(prog_files, "Directory", Id="INSTALLDIR", Name=project.targetName or project.name)
        comp = ET.SubElement(app_dir, "Component", Id="MainExecutable", Guid="*")
        file_elem = ET.SubElement(comp, "File", Id="ExeFile", Name=exe_path.name, Source=str(exe_path), KeyPath="yes")
        # Ajouter les DLLs
        for dep in project.dependFiles:
            dep_path = Path(dep)
            if dep_path.exists():
                ET.SubElement(comp, "File", Id=dep_path.stem, Name=dep_path.name, Source=str(dep_path))

        # Features
        feature = ET.SubElement(product, "Feature", Id="ProductFeature", Title=project.name, Level="1")
        ET.SubElement(feature, "ComponentRef", Id="MainExecutable")

        tree = ET.ElementTree(root)
        tree.write(output, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _GenerateInnoScript(project, builder, exe_path: Path, output: Path):
        """Génère un script Inno Setup."""
        script = f"""
[Setup]
AppName={project.targetName or project.name}
AppVersion={project.iosVersion or '1.0.0'}
DefaultDirName={{pf}}\\{project.targetName or project.name}
DefaultGroupName={project.targetName or project.name}
UninstallDisplayIcon={{app}}\\{exe_path.name}
Compression=lzma2
SolidCompression=yes
OutputDir=.
OutputBaseFilename={project.name}_setup

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"
"""
        for dep in project.dependFiles:
            dep_path = Path(dep)
            if dep_path.exists():
                script += f'Source: "{dep_path}"; DestDir: "{{app}}"\n'
        output.write_text(script, encoding='utf-8')

    # -----------------------------------------------------------------------
    # Linux
    # -----------------------------------------------------------------------

    @staticmethod
    def _PackageLinux(project, builder, pkg_type: str, output_dir: Path) -> int:
        """Création de packages Linux (deb, rpm, AppImage, Snap)."""
        if not builder.BuildProject(project):
            return 1

        exe_path = builder.GetTargetPath(project)
        if not exe_path.exists():
            Colored.PrintError(f"Executable not found: {exe_path}")
            return 1

        if pkg_type == 'deb':
            return PackageCommand._CreateDeb(project, builder, exe_path, output_dir)
        elif pkg_type == 'rpm':
            return PackageCommand._CreateRpm(project, builder, exe_path, output_dir)
        elif pkg_type == 'appimage':
            return PackageCommand._CreateAppImage(project, builder, exe_path, output_dir)
        elif pkg_type == 'snap':
            return PackageCommand._CreateSnap(project, builder, exe_path, output_dir)
        return 1

    @staticmethod
    def _CreateDeb(project, builder, exe_path: Path, output_dir: Path) -> int:
        """Crée un package .deb."""
        import subprocess
        # Vérifier la présence de dpkg-deb
        if not FileSystem.FindExecutable("dpkg-deb"):
            Colored.PrintError("dpkg-deb not found. Cannot create .deb package.")
            return 1

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # Créer la structure de dossier
            deb_root = tmp / "deb"
            usr_bin = deb_root / "usr" / "bin"
            usr_bin.mkdir(parents=True)
            shutil.copy2(exe_path, usr_bin / exe_path.name)

            # Créer le fichier DEBIAN/control
            control_dir = deb_root / "DEBIAN"
            control_dir.mkdir()
            control = f"""Package: {project.targetName or project.name}
Version: {project.iosVersion or '1.0.0'}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Jenga <team@jenga.build>
Description: {project.name} packaged by Jenga
"""
            (control_dir / "control").write_text(control, encoding='utf-8')

            # Construire le .deb
            deb_path = output_dir / f"{project.name}.deb"
            subprocess.run(["dpkg-deb", "--build", str(deb_root), str(deb_path)], check=True)
            Colored.PrintSuccess(f"DEB package: {deb_path}")
            return 0

    @staticmethod
    def _CreateRpm(project, builder, exe_path: Path, output_dir: Path) -> int:
        """Crée un package .rpm (nécessite rpmbuild)."""
        Colored.PrintWarning("RPM packaging not yet implemented.")
        return 1

    @staticmethod
    def _CreateAppImage(project, builder, exe_path: Path, output_dir: Path) -> int:
        """Crée un AppImage (nécessite appimagetool)."""
        Colored.PrintWarning("AppImage packaging not yet implemented.")
        return 1

    @staticmethod
    def _CreateSnap(project, builder, exe_path: Path, output_dir: Path) -> int:
        """Crée un Snap package (nécessite snapcraft)."""
        Colored.PrintWarning("Snap packaging not yet implemented.")
        return 1

    # -----------------------------------------------------------------------
    # macOS
    # -----------------------------------------------------------------------

    @staticmethod
    def _PackageMacOS(project, builder, pkg_type: str, output_dir: Path) -> int:
        """Création de package macOS (PKG, DMG)."""
        if not builder.BuildProject(project):
            return 1

        if pkg_type == 'pkg':
            # Utiliser pkgbuild
            if not FileSystem.FindExecutable("pkgbuild"):
                Colored.PrintError("pkgbuild not found (macOS required).")
                return 1
            app_bundle = builder.GetTargetDir(project) / f"{project.targetName or project.name}.app"
            if not app_bundle.exists():
                Colored.PrintError(f".app bundle not found: {app_bundle}")
                return 1
            pkg_path = output_dir / f"{project.name}.pkg"
            cmd = ["pkgbuild", "--root", str(app_bundle.parent), "--identifier", project.iosBundleId or f"com.{project.name}",
                   "--version", project.iosVersion or "1.0.0", str(pkg_path)]
            if Process.Run(cmd) == 0:
                Colored.PrintSuccess(f"PKG package: {pkg_path}")
                return 0
            return 1

        elif pkg_type == 'dmg':
            # Utiliser create-dmg
            if not FileSystem.FindExecutable("create-dmg"):
                Colored.PrintWarning("create-dmg not found. Install with: brew install create-dmg")
                return 1
            app_bundle = builder.GetTargetDir(project) / f"{project.targetName or project.name}.app"
            if not app_bundle.exists():
                return 1
            dmg_path = output_dir / f"{project.name}.dmg"
            cmd = ["create-dmg", "--volname", project.name, str(dmg_path), str(app_bundle)]
            if Process.Run(cmd) == 0:
                Colored.PrintSuccess(f"DMG package: {dmg_path}")
                return 0
            return 1

        return 1

    # -----------------------------------------------------------------------
    # Web (Emscripten)
    # -----------------------------------------------------------------------

    @staticmethod
    def _PackageWeb(project, builder, pkg_type: str, output_dir: Path) -> int:
        """Création d'un ZIP pour WebAssembly."""
        if pkg_type != 'zip':
            Colored.PrintError("Only ZIP packaging is supported for Web platform.")
            return 1
        if not builder.BuildProject(project):
            return 1

        target_dir = builder.GetTargetDir(project)
        # Rechercher .html, .js, .wasm
        import zipfile
        zip_path = output_dir / f"{project.targetName or project.name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for ext in ['.html', '.js', '.wasm', '.data']:
                for f in target_dir.glob(f"*{ext}"):
                    zf.write(f, f.name)
        Colored.PrintSuccess(f"Web ZIP package: {zip_path}")
        return 0
