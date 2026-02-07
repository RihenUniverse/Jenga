#!/usr/bin/env python3
"""
Script d'installation pour configurer Jenga correctement
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_vscode_config():
    """Configure VS Code pour reconnaître les fichiers .jenga"""
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    settings = {
        "files.associations": {
            "*.jenga": "python"
        },
        "python.analysis.extraPaths": ["./Jenga"],
        "python.linting.enabled": True,
        "python.analysis.typeCheckingMode": "basic"
    }
    
    import json
    settings_file = vscode_dir / "settings.json"
    settings_file.write_text(json.dumps(settings, indent=2))
    
    print("✅ Configuration VS Code créée")

def create_py_typed():
    """Crée le fichier py.typed"""
    py_typed = Path("Jenga/py.typed")
    py_typed.touch()
    print("✅ Fichier py.typed créé")

def install_package():
    """Installe le package avec pip"""
    print("📦 Installation de Jenga...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
    print("✅ Jenga installé avec succès")

if __name__ == "__main__":
    create_py_typed()
    setup_vscode_config()
    install_package()
    print("\n🎉 Installation terminée!")
    print("Les fichiers .jenga sont maintenant reconnus comme Python.")
    print("Vous pouvez utiliser: import Jenga.core.api")