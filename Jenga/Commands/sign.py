#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sign command – Signe un APK Android ou IPA iOS.
Délègue aux builders spécifiques.
"""

import argparse
import sys, os
from pathlib import Path
from typing import List, Optional, Tuple

from ..Utils import Colored, FileSystem
from ..Core.Loader import Loader
from ..Core.Cache import Cache
from ..Core.Platform import Platform
from ..Core import Api


class SignCommand:
    """jenga sign --apk FILE [--keystore KS] [--alias ALIAS] [--storepass PASS] [--keypass PASS]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(
            prog="jenga sign",
            description="Sign an Android APK or iOS IPA."
        )
        parser.add_argument("--apk", help="Android APK file to sign")
        parser.add_argument("--ipa", help="iOS IPA file to sign")
        parser.add_argument("--keystore", help="Keystore file (Android)")
        parser.add_argument("--alias", help="Key alias")
        parser.add_argument("--storepass", help="Keystore password")
        parser.add_argument("--keypass", help="Key password")
        parser.add_argument("--project", help="Project name (to get signing config)")
        parser.add_argument("--no-daemon", action="store_true", help="Do not use daemon")
        parser.add_argument("--jenga-file", help="Path to the workspace .jenga file (default: auto-detected)")
        parsed = parser.parse_args(args)

        if not parsed.apk and not parsed.ipa:
            Colored.PrintError("Specify either --apk or --ipa.")
            return 1

        if parsed.apk:
            return SignCommand._SignAndroid(parsed)
        else:
            return SignCommand._SignIOS(parsed)

    @staticmethod
    def _SignAndroid(args) -> int:
        """Signe un APK avec apksigner."""
        # Si un projet est spécifié, charger ses paramètres depuis le workspace
        keystore = args.keystore
        alias = args.alias
        storepass = args.storepass
        keypass = args.keypass

        if args.project:
            # Déterminer le répertoire de travail (workspace root)
            workspace_root = Path.cwd()
            if args.jenga_file:
                entry_file = Path(args.jenga_file).resolve()
                if not entry_file.exists():
                    Colored.PrintError(f"Jenga file not found: {entry_file}")
                    return 1
            else:
                entry_file = FileSystem.FindWorkspaceEntry(workspace_root)
                if not entry_file:
                    Colored.PrintError("No .jenga workspace file found.")
                    return 1
            workspace_root = entry_file.parent
            
            if entry_file:
                loader = Loader()
                cache = Cache(entry_file.parent, workspaceName=entry_file.stem)
                workspace = cache.LoadWorkspace(entry_file, loader)
                if workspace and args.project in workspace.projects:
                    proj = workspace.projects[args.project]
                    keystore = keystore or proj.androidKeystore
                    alias = alias or proj.androidKeyAlias
                    storepass = storepass or proj.androidKeystorePass
                    # keypass = keypass or proj.androidKeyPass? (pas dans l'API actuelle)

        if not keystore or not Path(keystore).exists():
            Colored.PrintError("Keystore not found. Provide --keystore or configure in project.")
            return 1

        # Chercher apksigner dans le SDK Android
        apksigner = SignCommand._FindApksigner()
        if not apksigner:
            Colored.PrintError("apksigner not found. Install Android SDK build-tools.")
            return 1

        cmd = [
            apksigner, "sign",
            "--ks", keystore,
            "--ks-pass", f"pass:{storepass or ''}",
            "--ks-key-alias", alias or "mykey",
            "--out", str(Path(args.apk).with_suffix(".signed.apk")),
            args.apk
        ]
        if keypass:
            cmd.extend(["--key-pass", f"pass:{keypass}"])

        Colored.PrintInfo(f"Signing {args.apk}...")
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            Colored.PrintSuccess(f"Signed APK created.")
            return 0
        else:
            Colored.PrintError(f"Signing failed: {result.stderr}")
            return 1

    @staticmethod
    def _SignIOS(args) -> int:
        """Signe un IPA avec codesign (nécessite macOS)."""
        if Platform.GetHostOS() != Api.TargetOS.MACOS:
            Colored.PrintError("iOS signing requires macOS.")
            return 1
        # Déléguer à xcodebuild / codesign
        Colored.PrintInfo("iOS signing not yet implemented.")
        return 1

    @staticmethod
    def _FindApksigner() -> str:
        """Localise apksigner dans le SDK Android."""
        # Chercher dans les variables d'environnement
        sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        if sdk:
            sdk_path = Path(sdk)
            bt_dir = sdk_path / "build-tools"
            if bt_dir.exists():
                versions = sorted([d for d in bt_dir.iterdir() if d.is_dir()], reverse=True)
                for ver in versions:
                    apk = ver / "apksigner"
                    if sys.platform == "win32":
                        apk = apk.with_suffix(".exe")
                    if apk.exists():
                        return str(apk)
        # Fallback: which
        return FileSystem.FindExecutable("apksigner") or ""
