#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keygen command – Génère une keystore pour la signature Android.
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from ..Utils import Colored, FileSystem, Display


class KeygenCommand:
    """jenga keygen [--alias ALIAS] [--validity DAYS] [--output FILE]"""

    @staticmethod
    def Execute(args: List[str]) -> int:
        parser = argparse.ArgumentParser(
            prog="jenga keygen",
            description="Generate a keystore for Android app signing."
        )
        parser.add_argument("--alias", default="mykey", help="Key alias (default: mykey)")
        parser.add_argument("--validity", type=int, default=10000, help="Validity in days (default: 10000)")
        parser.add_argument("--output", "-o", help="Output keystore file (default: ./keystore.jks)")
        parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
        parsed = parser.parse_args(args)

        # Détecter keytool (Java)
        keytool = FileSystem.FindExecutable("keytool")
        if not keytool:
            Colored.PrintError("keytool not found. Please install Java JDK.")
            return 1

        # Déterminer le fichier de sortie
        if parsed.output:
            keystore_path = Path(parsed.output)
        else:
            keystore_path = Path.cwd() / "keystore.jks"

        if keystore_path.exists():
            overwrite = Display.Prompt(f"Keystore already exists. Overwrite?", default="n")
            if overwrite.lower() not in ('y', 'yes'):
                Colored.PrintInfo("Cancelled.")
                return 0

        # Mode interactif
        if parsed.interactive:
            Display.Section("Generate Android Keystore")
            alias = Display.Prompt("Key alias", default=parsed.alias)
            validity = int(Display.Prompt("Validity (days)", default=str(parsed.validity)))
            dn = Display.Prompt("Distinguished Name (CN=Name, OU=Org, O=Company, L=City, ST=State, C=Country)",
                                default="CN=Jenga User")
            password = Display.PromptPassword("Keystore password")
            key_password = Display.PromptPassword("Key password (default: same as keystore)", allow_empty=True)
            if not key_password:
                key_password = password
        else:
            alias = parsed.alias
            validity = parsed.validity
            dn = "CN=Jenga User, OU=Development, O=Jenga, L=Unknown, ST=Unknown, C=US"
            password = "android"
            key_password = "android"

        # Construire la commande keytool
        cmd = [
            keytool, "-genkeypair",
            "-alias", alias,
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", str(validity),
            "-keystore", str(keystore_path),
            "-storepass", password,
            "-keypass", key_password,
            "-dname", dn
        ]

        Colored.PrintInfo("Generating keystore...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                Colored.PrintSuccess(f"Keystore generated: {keystore_path}")
                Colored.PrintInfo(f"Alias: {alias}")
                return 0
            else:
                Colored.PrintError(f"Keytool failed: {result.stderr}")
                return 1
        except Exception as e:
            Colored.PrintError(f"Error: {e}")
            return 1
