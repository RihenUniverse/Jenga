# 🔧 Jenga Build System - Guide de Dépannage

## ⚠ Problème: "__Unitest__ - No source files found"

### Symptôme
```
Building project: __Unitest__
⚠ No source files found for project __Unitest__
```

### Cause
Le projet `__Unitest__` auto-injecté ne trouve pas ses fichiers sources.

### Solutions

#### Solution 1: Vérifier la Structure de Fichiers

**Structure attendue** :

Option A (dans Tools/) :
```
Tools/
└── jenga/              # Minuscule !
    └── Unitest/
        └── src/
            └── Unitest/
                ├── Unitest.cpp
                ├── Unitest.h
                ├── TestCase.cpp
                └── ... (autres fichiers)
```

Option B (dans workspace root) :
```
Workspace/
└── Unitest/
    └── src/
        └── Unitest/
            ├── Unitest.cpp
            ├── Unitest.h
            └── ...
```

#### Solution 2: Créer le Dossier Unitest

Si Unitest n'existe pas, créez-le :

**Windows** :
```cmd
mkdir Unitest\src\Unitest
```

**Linux/Mac** :
```bash
mkdir -p Unitest/src/Unitest
```

Puis copiez les fichiers depuis `Tools/jenga/Unitest/` :
```cmd
xcopy /E Tools\jenga\Unitest\src Unitest\src\
```

#### Solution 3: Modifier jenga.jenga

Si vous avez déjà un projet Unitest dans votre workspace, le système détectera automatiquement le doublon. Vous pouvez :

**Option A** : Renommer votre projet
```python
with project("MyUnitest"):  # Au lieu de "Unitest"
    staticlib()
    # ...
```

**Option B** : Désactiver l'auto-injection
```python
# Actuellement non supporté, mais à venir dans v1.1
```

#### Solution 4: Vérifier les Chemins

Le système cherche Unitest dans cet ordre :

1. `Tools/jenga/Unitest/` (chemin relatif à api.py)
2. `Unitest/` (workspace root)

Vérifiez que l'un de ces chemins existe :

```python
# Diagnostic Python
from pathlib import Path
import sys

# Chemin Tools
tools_dir = Path("Tools")
unitest1 = tools_dir / "jenga" / "Unitest" / "src" / "Unitest"
print(f"Tools/jenga/Unitest exists: {unitest1.exists()}")

# Chemin workspace
unitest2 = Path("Unitest") / "src" / "Unitest"
print(f"Unitest/ exists: {unitest2.exists()}")
```

### Fix Rapide

**Copier Unitest à la racine du workspace** :

```cmd
# Windows
xcopy /E /I Tools\jenga\Unitest Unitest

# Linux/Mac
cp -r Tools/jenga/Unitest Unitest
```

Puis rebuild :
```bash
jenga rebuild
```

---

## 🔍 Autres Problèmes Courants

### Problème: "Configuration file not found"

**Symptôme** :
```
✗ Configuration file not found: *.jenga
```

**Solution** :
Créez un fichier `.jenga` dans le dossier courant ou spécifiez le chemin :
```bash
jenga build --config path/to/config.jenga
```

### Problème: "Platform not detected"

**Symptôme** :
```
✗ Could not detect platform
```

**Solution** :
Spécifiez manuellement :
```bash
jenga build --platform Windows
jenga build --platform Linux
```

### Problème: "Compiler not found"

**Symptôme** :
```
✗ Compiler 'g++' not found
```

**Solutions** :

**Windows** :
1. Installez MinGW-w64 ou MSVC
2. Ajoutez au PATH
3. Ou utilisez MSVC :
```python
with toolchain("msvc", "cl"):
    cppcompiler("cl")
```

**Linux** :
```bash
sudo apt-get install build-essential
```

**Mac** :
```bash
xcode-select --install
```

### Problème: "Permission denied" (Linux/Mac)

**Symptôme** :
```
bash: ./jenga.sh: Permission denied
```

**Solution** :
```bash
chmod +x jenga.sh
./jenga.sh build
```

### Problème: Build lent (pas de cache)

**Symptôme** :
Build prend trop de temps, fichiers recompilés à chaque fois.

**Solution** :

1. Vérifiez que `.cjenga/` existe :
```bash
ls -la .cjenga/
```

2. Si absent, créez-le :
```bash
mkdir .cjenga
```

3. Vérifiez les permissions :
```bash
chmod 755 .cjenga
```

### Problème: "Module not found" (Python)

**Symptôme** :
```
ModuleNotFoundError: No module named 'jenga'
```

**Solution** :

**Option 1** : Utiliser les wrappers
```bash
# Au lieu de python Tools/jenga.py
./jenga.sh build    # Linux/Mac
jenga.bat build     # Windows
```

**Option 2** : Ajouter au PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/Tools"
python -m jenga build
```

### Problème: Android SDK non trouvé

**Symptôme** :
```
✗ Android SDK path not set in workspace
```

**Solution** :

Dans votre `.jenga` :
```python
with workspace("MyApp"):
    androidsdkpath("C:/Users/YourName/AppData/Local/Android/Sdk")  # Windows
    # ou
    androidsdkpath("/home/user/Android/Sdk")  # Linux
```

Ou variable d'environnement :
```bash
export ANDROID_SDK_ROOT=/path/to/sdk
```

### Problème: "Keystore not found"

**Symptôme** :
```
✗ Keystore not found: release.jks
```

**Solution** :

Générer un keystore :
```bash
jenga keygen --platform Android
```

Ou utiliser keytool directement :
```bash
keytool -genkeypair -v -keystore release.jks -alias key0 \
  -keyalg RSA -keysize 2048 -validity 10000
```

---

## 📊 Diagnostic Complet

### Script de Diagnostic

Créez `diagnose.py` :

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

print("=== Jenga Build System Diagnostic ===\n")

# 1. Python version
print(f"Python: {sys.version}")

# 2. Structure
print("\n=== File Structure ===")
checks = [
    ("Tools/jenga/core/api.py", "Core API"),
    ("Tools/jenga/Unitest/src/Unitest/Unitest.cpp", "Unitest (Tools)"),
    ("Unitest/src/Unitest/Unitest.cpp", "Unitest (Root)"),
    (".cjenga/cbuild.json", "Build Cache"),
]

for path, desc in checks:
    exists = "✓" if Path(path).exists() else "✗"
    print(f"{exists} {desc}: {path}")

# 3. Jenga file
jenga_files = list(Path(".").glob("*.jenga"))
print(f"\n=== Jenga Files ===")
if jenga_files:
    for f in jenga_files:
        print(f"✓ {f}")
else:
    print("✗ No .jenga file found")

# 4. Compilers
print("\n=== Compilers ===")
import shutil
compilers = ["g++", "clang++", "cl"]
for compiler in compilers:
    path = shutil.which(compiler)
    if path:
        print(f"✓ {compiler}: {path}")
    else:
        print(f"✗ {compiler}: not found")

print("\n=== End Diagnostic ===")
```

Exécutez :
```bash
python diagnose.py
```

---

## 🆘 Support

Si le problème persiste :

1. **Vérifiez les logs** : `.cjenga/cbuild.json`
2. **Mode verbose** : `jenga build --verbose`
3. **Clean rebuild** : `jenga clean && jenga rebuild`
4. **Vérifiez la structure** : `tree /f` (Windows) ou `tree` (Linux)

### Informations à Fournir

Lors d'une demande d'aide, incluez :

```bash
# Version
jenga --version

# Info
jenga info

# Structure
tree -L 3

# Diagnostic
python diagnose.py

# Erreur complète
jenga build --verbose 2>&1 | tee build.log
```

---

## ✅ Checklist de Vérification

Avant de builder, vérifiez :

- [ ] Python 3.7+ installé
- [ ] Fichier `.jenga` présent
- [ ] Compiler installé et dans PATH
- [ ] Dossier `.cjenga/` avec permissions
- [ ] Structure Unitest correcte (si utilisant tests)
- [ ] Android SDK configuré (si Android)
- [ ] Permissions exécution sur jenga.sh/bat

---

## 🎯 Fix Unitest - Résumé Rapide

**Problème** : `__Unitest__` ne trouve pas ses sources

**Fix Immédiat** :
```bash
# 1. Copier Unitest
cp -r Tools/jenga/Unitest Unitest

# 2. Rebuild
jenga clean
jenga rebuild

# ✓ Devrait fonctionner !
```

**Explication** : Le système cherche `Unitest/src/Unitest/` à la racine du workspace. Si absent, copiez-le depuis `Tools/jenga/Unitest/`.

---

**Version** : Jenga Build System v1.0.0
**Dernière mise à jour** : 2026-01-23
