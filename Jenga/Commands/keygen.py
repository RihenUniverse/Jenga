#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jenga Build System - Keygen Command
Generates keystores for signing applications (Android, etc.)
"""

import sys
import subprocess
import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_workspace
from utils.display import Display, Colors


def execute(options: dict) -> bool:
    """Execute keygen command"""
    
    platform = options.get('platform', 'Android')
    
    Display.section(f"Keystore Generator - {platform}")
    
    if platform == 'Android':
        return _generate_android_keystore(options)
    else:
        Display.error(f"Keystore generation not supported for: {platform}")
        return False


def _generate_android_keystore(options):
    """Generate Android keystore using keytool"""
    
    Display.step("Generating Android keystore...")
    
    # Get parameters
    keystore_name = options.get('name') or input("Keystore name (default: release.jks): ").strip() or "release.jks"
    
    if not keystore_name.endswith('.jks') and not keystore_name.endswith('.keystore'):
        keystore_name += '.jks'
    
    keystore_path = Path(keystore_name)
    
    if keystore_path.exists():
        Display.warning(f"Keystore already exists: {keystore_path}")
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            Display.info("Cancelled")
            return False
    
    # Get keystore details
    print()
    Display.info("Enter keystore details:")
    
    alias = options.get('alias') or input("  Key alias (default: key0): ").strip() or "key0"
    
    # Password
    if options.get('storepass'):
        store_pass = options.get('storepass')
    else:
        while True:
            store_pass = getpass.getpass("  Keystore password (min 6 chars): ")
            if len(store_pass) < 6:
                Display.error("Password must be at least 6 characters")
                continue
            store_pass_confirm = getpass.getpass("  Confirm password: ")
            if store_pass != store_pass_confirm:
                Display.error("Passwords don't match")
                continue
            break
    
    # Certificate details
    print()
    Display.info("Certificate details (press Enter for defaults):")
    
    cn = input("  Your name (CN): ").strip() or "Developer"
    ou = input("  Organization Unit (OU): ").strip() or "Development"
    o = input("  Organization (O): ").strip() or "MyCompany"
    l = input("  City/Locality (L): ").strip() or "City"
    st = input("  State/Province (ST): ").strip() or "State"
    c = input("  Country Code (C, 2 letters): ").strip() or "US"
    
    validity = options.get('validity') or input("  Validity (days, default: 10000): ").strip() or "10000"
    
    # Build dname
    dname = f"CN={cn}, OU={ou}, O={o}, L={l}, ST={st}, C={c}"
    
    Display.info(f"\nGenerating keystore: {keystore_path}")
    Display.info(f"Alias: {alias}")
    Display.info(f"DN: {dname}")
    Display.info(f"Validity: {validity} days")
    
    # Generate keystore with keytool
    try:
        cmd = [
            "keytool",
            "-genkeypair",
            "-v",
            "-keystore", str(keystore_path),
            "-alias", alias,
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", validity,
            "-storepass", store_pass,
            "-keypass", store_pass,
            "-dname", dname
        ]
        
        Display.info("\nGenerating keypair...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            Display.error("Failed to generate keystore:")
            print(result.stderr)
            
            # Check if keytool is available
            which_result = subprocess.run(["which", "keytool"], capture_output=True)
            if which_result.returncode != 0:
                Display.error("\nkeytool not found!")
                Display.info("keytool is part of the Java Development Kit (JDK)")
                Display.info("Install JDK and ensure keytool is in your PATH")
            
            return False
        
        Display.success(f"\n✓ Keystore generated successfully!")
        Display.info(f"\nKeystore: {keystore_path.absolute()}")
        Display.info(f"Alias: {alias}")
        
        # Show how to use it
        Display.section("How to use this keystore")
        
        print(f"""
Add to your .jenga file:

    with project("MyApp"):
        # ... other settings ...
        
        # Android signing
        androidsign(True)
        androidkeystore("{keystore_path.absolute()}")
        androidkeystorepass("{store_pass}")
        androidkeyalias("{alias}")

Then build and sign:

    jenga package --platform Android
    # or
    jenga sign --platform Android --keystore {keystore_path}
        """)
        
        Display.warning("⚠ Keep your keystore and password safe!")
        Display.info("  • Never commit keystore to version control")
        Display.info("  • Backup your keystore securely")
        Display.info("  • Losing the keystore means you cannot update your app on Play Store")
        
        return True
        
    except FileNotFoundError:
        Display.error("keytool command not found")
        Display.info("Install Java Development Kit (JDK) to use keytool")
        Display.info("  • Ubuntu/Debian: sudo apt-get install default-jdk")
        Display.info("  • macOS: brew install openjdk")
        Display.info("  • Windows: Download from https://adoptium.net/")
        return False
    
    except Exception as e:
        Display.error(f"Error generating keystore: {e}")
        return False


if __name__ == "__main__":
    execute({})