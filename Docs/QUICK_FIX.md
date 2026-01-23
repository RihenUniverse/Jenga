# 🚀 Jenga Build System - Fix Rapide Unitest

## ⚠ Problème Rencontré

```
Building project: __Unitest__
⚠ No source files found for project __Unitest__
```

## ✅ Solution Immédiate (Windows)

Ouvrez PowerShell dans votre dossier Jenga et exécutez :

```powershell
# Copier Unitest à la racine
xcopy /E /I Tools\jenga\Unitest Unitest

# Rebuild
.\jenga.bat clean
.\jenga.bat build
```

## ✅ Solution Immédiate (Linux/Mac)

```bash
# Copier Unitest à la racine
cp -r Tools/jenga/Unitest Unitest

# Rebuild
./jenga.sh clean
./jenga.sh build
```

## 🔍 Diagnostic Automatique

Pour vérifier votre installation :

```bash
python diagnose.py
```

Ce script vérifiera :
- ✓ Python version
- ✓ Structure des fichiers
- ✓ Unitest framework
- ✓ Compilateurs disponibles
- ✓ Fichiers de configuration

## 📋 Vérification Manuelle

Assurez-vous que cette structure existe :

```
Votre_Projet/
├── Unitest/              ← DOIT EXISTER !
│   └── src/
│       └── Unitest/
│           ├── Unitest.cpp
│           ├── Unitest.h
│           └── ... (autres fichiers)
├── Tools/
│   └── jenga/
│       └── Unitest/      ← Source originale
└── *.jenga               ← Votre configuration
```

## 🎯 Pourquoi Ce Fix ?

Le système auto-injecte un projet `__Unitest__` pour les tests unitaires. Ce projet cherche ses sources dans :

1. **Priorité 1** : `Tools/jenga/Unitest/` (chemin relatif à api.py)
2. **Priorité 2** : `Unitest/` (racine workspace)

Sur Windows, le chemin `Tools/jenga/Unitest` (avec `jenga` en minuscule) doit exister.

Le fix consiste à copier Unitest à la racine pour que tous les workspaces y aient accès.

## 📚 Documentation Complète

Consultez **TROUBLESHOOTING.md** pour :
- Problèmes courants et solutions
- Guide de diagnostic complet
- Erreurs de compilation
- Configuration Android
- Et plus...

## 🆘 Toujours des Problèmes ?

1. **Exécutez le diagnostic** :
   ```bash
   python diagnose.py
   ```

2. **Mode verbose** :
   ```bash
   jenga build --verbose
   ```

3. **Clean rebuild** :
   ```bash
   jenga clean
   jenga rebuild
   ```

4. **Vérifiez la structure** :
   ```cmd
   tree /f    # Windows
   tree       # Linux/Mac
   ```

## ✨ Après le Fix

Une fois Unitest copié, vous devriez voir :

```
Building project: __Unitest__
ℹ Found 11 source file(s)
✓ Compiled: Unitest.cpp
✓ Compiled: TestCase.cpp
...
✓ Built: Build/Lib/Debug/__Unitest__.lib
```

## 🎉 Succès !

Après le fix, votre build devrait réussir complètement :

```
✓ Build completed in 7.87s
✓ Build completed successfully
```

---

**Version** : Jenga Build System v1.0.0
**Date** : 2026-01-23
**Support** : Voir TROUBLESHOOTING.md
