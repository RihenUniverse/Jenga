# Builders Archivés (unused/)

Ce dossier contient des versions obsolètes ou alternatives de builders qui ont été consolidées lors de la mise en production de Jenga v2.0.0.

## Raisons de l'archivage

Les fichiers ici présents représentent des étapes intermédiaires de développement ou des approches alternatives qui ne sont plus utilisées dans la version principale.

---

## Android Builders

### `Android_original.py`
- **Version** : Originale (16 févr. 2024)
- **Taille** : 967 lignes
- **Raison** : Version de base remplacée par une version plus complète
- **Limitations** :
  - Pas de support Java (javac)
  - Pas de ProGuard/R8
  - Console apps non supportées (uniquement .so libraries)

### `Android01.py`
- **Version** : Première amélioration (18 févr. 2024 19:55)
- **Taille** : 1,256 lignes
- **Améliorations** : Support console executables
- **Raison** : Version intermédiaire

### `Android02.py`
- **Version** : Deuxième amélioration (18 févr. 2024 20:10)
- **Taille** : 1,353 lignes
- **Améliorations** : Support compilation Java (javac), multi-DEX
- **Raison** : Version intermédiaire

### `Android03.py`
- **Version** : Version finale consolidée (18 févr. 2024 20:16)
- **Taille** : 1,354 lignes
- **Améliorations** : ProGuard/R8 obfuscation
- **Status** : **UTILISÉE** - Contenu copié dans `Android.py`

---

## iOS Builders

### `Ios_original.py`
- **Version** : Originale (17 févr. 2024 13:55)
- **Taille** : 464 lignes
- **Approche** : Direct compilation (clang)
- **Raison** : Remplacée par DirectIOSBuilder

### `DirectIOSBuilder.py`
- **Version** : Builder direct (17 févr. 2024 20:08)
- **Taille** : 526 lignes
- **Approche** : Compilation directe sans Xcode
- **Status** : **UTILISÉE** - Contenu copié dans `Ios.py`
- **Avantages** :
  - Indépendant de Xcode
  - Optimal pour CI/CD
  - Builds plus rapides
  - Pas de dépendances IDE

### `IosUseXBuilder.py`
- **Version** : Builder avec Xcode (17 févr. 2024 13:55)
- **Taille** : 659 lignes
- **Approche** : Utilise Xcode pour la compilation
- **Raison** : Approche alternative non retenue

### `XcodeIOSBuilder.py`
- **Version** : Xcode spécifique iOS (18 févr. 2024 20:21)
- **Taille** : 688 lignes
- **Approche** : Xcode pour iOS uniquement
- **Raison** : Consolidé dans MacosXcodeBuilder.py

### `XcodeMobileBuilder.py`
- **Version** : Xcode multi-plateformes (17 févr. 2024 20:20)
- **Taille** : 775 lignes (le plus complet)
- **Approche** : Xcode pour toutes plateformes Apple (iOS, tvOS, watchOS)
- **Status** : **CONSERVÉ** comme `MacosXcodeBuilder.py` pour mode Xcode
- **Usage** : Activable via `apple_mobile_mode="xcode"`

### `XcodeMobileBuilder01.py`
- **Version** : Variante simplifiée (18 févr. 2024 20:34)
- **Taille** : 381 lignes
- **Raison** : Version simplifiée non retenue

### `AppleMobileBuilder.py`
- **Version** : Abstraction générique (18 févr. 2024 20:50)
- **Taille** : 335 lignes
- **Approche** : Builder générique Apple
- **Raison** : Approche trop abstraite

### `XcrunMobileBuilder.py`
- **Version** : Basée sur xcrun (18 févr. 2024 20:24)
- **Taille** : 106 lignes
- **Approche** : Utilise xcrun directement
- **Raison** : Trop bas niveau

### `XcrunMobileBuilder01.py`
- **Version** : Variante xcrun avancée (18 févr. 2024 20:45)
- **Taille** : 290 lignes
- **Raison** : Approche alternative non retenue

---

## Emscripten Builders

### `Emscripten_original.py`
- **Version** : Originale (18 févr. 2024 21:44)
- **Taille** : 245 lignes
- **Raison** : Remplacée par version avec meilleure documentation

### `Emscripten01.py`
- **Version** : Avec documentation (19 févr. 2024 02:48)
- **Taille** : 249 lignes
- **Amélioration** : Commentaires de documentation ajoutés
- **Status** : **UTILISÉE** - Contenu copié dans `Emscripten.py`
- **Différence** : 4 lignes de commentaires seulement

---

## Xbox Builders

### `Xbox_original.py`
- **Version** : Originale (17 févr. 2024 14:37)
- **Taille** : 780 lignes
- **Raison** : Remplacée par version avec meilleure documentation

### `Xbox01.py`
- **Version** : Avec documentation (18 févr. 2024 21:10)
- **Taille** : 809 lignes
- **Amélioration** : Documentation et commentaires améliorés
- **Status** : **UTILISÉE** - Contenu copié dans `Xbox.py`
- **Différence** : 29 lignes (principalement commentaires)

---

## Builders Actifs (versions consolidées)

Les fichiers suivants dans le dossier parent sont les versions **actuellement utilisées** :

| Plateforme | Fichier actif | Source | Approche |
|-----------|--------------|---------|----------|
| Android | `Android.py` | Android03.py | NDK + Java + ProGuard |
| iOS/tvOS/watchOS | `Ios.py` | DirectIOSBuilder.py | Direct compilation (prioritaire) |
| iOS/macOS (mode Xcode) | `MacosXcodeBuilder.py` | XcodeMobileBuilder.py | Xcode (alternatif) |
| WebAssembly | `Emscripten.py` | Emscripten01.py | Emscripten SDK |
| Xbox Series | `Xbox.py` | Xbox01.py | MSVC + GDK |
| Windows | `Windows.py` | - | MSVC/MinGW |
| Linux | `Linux.py` | - | GCC/Clang |
| macOS | `Macos.py` | - | Clang (prioritaire) |
| HarmonyOS | `HarmonyOs.py` | - | HarmonyOS NDK |

---

## Modes de Compilation Apple

Le système supporte **deux modes** pour les plateformes Apple (iOS, tvOS, watchOS, macOS) :

### Mode "direct" (par défaut)
```python
# Utilise Ios.py ou Macos.py
builder = get_builder_class("iOS", apple_mobile_mode="direct")
```
- ✅ Compilation directe via clang
- ✅ Indépendant de Xcode
- ✅ Optimal pour CI/CD
- ✅ Builds rapides

### Mode "xcode" (alternatif)
```python
# Utilise MacosXcodeBuilder.py
builder = get_builder_class("iOS", apple_mobile_mode="xcode")
```
- ✅ Utilise Xcode pour générer et compiler
- ✅ Meilleure compatibilité App Store
- ✅ Support complet des frameworks Apple
- ⚠️ Nécessite Xcode installé

---

## Réactivation d'un Builder

Si nécessaire, un builder archivé peut être réactivé :

1. **Copier** le fichier depuis `unused/` vers le dossier parent
2. **Mettre à jour** `__init__.py` pour référencer le nouveau builder
3. **Tester** la compilation avec un exemple

Exemple :
```bash
cp unused/XcodeIOSBuilder.py ../MyCustomBuilder.py
# Éditer __init__.py pour ajouter le mapping
```

---

## Historique de Consolidation

**Date** : 22 février 2026
**Version** : Jenga v2.0.0
**Raison** : Mise en production - Élimination des duplications
**Builders consolidés** : 4 plateformes (Android, iOS, Emscripten, Xbox)
**Builders archivés** : 14 fichiers

---

## Notes

- Les fichiers archivés sont **conservés pour référence** et peuvent servir de base pour de futures améliorations
- Pour **macOS**, la version Xcode (`MacosXcodeBuilder.py`) reste disponible dans le dossier parent comme alternative
- La consolidation a permis de **réduire la complexité** tout en **préservant toutes les fonctionnalités**
