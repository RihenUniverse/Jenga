# Jenga Build System - Changements Majeurs v1.0

## 🎉 Rebranding: Nken → Jenga

### Nouveaux Noms
- **Commande**: `jenga` (au lieu de `nken`)
- **Extension**: `.jenga` (au lieu de `.nken`)
- **Cache**: `.cjenga/` (au lieu de `.nken_cache/`)
- **Fichier cache**: `cbuild.json` (au lieu de `build_cache.json`)

### Logo JENGA
```
╔══════════════════════════════════════════════════════════════════╗
║                                                                      ║
║            ██╗███████╗███╗   ██╗ ██████╗  █████╗                    ║
║            ██║██╔════╝████╗  ██║██╔════╝ ██╔══██╗                   ║
║            ██║█████╗  ██╔██╗ ██║██║  ███╗███████║                   ║
║       ██   ██║██╔══╝  ██║╚██╗██║██║   ██║██╔══██║                   ║
║       ╚█████╔╝███████╗██║ ╚████║╚██████╔╝██║  ██║                   ║
║        ╚════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝                   ║
║                                                                      ║
║    Multi-platform C/C++ Build System v1.0.0                       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════╝
```

## 📁 Structure des Fichiers

### Ancienne Structure
```
MyProject/
├── myproject.nken
├── .nken_cache/
│   └── build_cache.json
└── Tools/
    └── nken.py
```

### Nouvelle Structure
```
MyProject/
├── myproject.jenga
├── .cjenga/
│   └── cbuild.json
└── Tools/
    ├── jenga.py
    └── Jenga/           # Unitest auto-intégré
        └── ...
```

## 🔧 Utilisation

### Commandes de Base
```bash
# Avant
nken build
nken clean
nken run

# Maintenant
jenga build
jenga clean
jenga run
```

### Fichier de Configuration
```python
# myproject.jenga

# Imports automatiquement commentés par le loader
# from jenga.core.api import *  # Auto-commenté

with workspace("MyProject"):
    configurations(["Debug", "Release"])
    
    with project("Core"):
        staticlib()
        # ...
```

## ✨ Nouvelles Fonctionnalités

### 1. Auto-Commentaire des Imports
Les lignes `from jenga.*` sont automatiquement commentées lors du chargement :
```python
# Avant chargement:
from jenga.core.api import *

# Après chargement automatique:
# from jenga.core.api import *  # Auto-commented by Jenga loader
```

### 2. Cache Optimisé
- **20x plus rapide** avec mtime+size
- Dossier: `.cjenga/`
- Fichier: `cbuild.json`

### 3. Compilation Parallèle
```bash
jenga build --jobs 8  # 8 threads parallèles
```

### 4. Tests Automatiques
```python
with test("MyTests"):
    testfiles(["tests/**.cpp"])
    testmainfile("src/main.cpp")
    testoptions(["--verbose", "--parallel"])
```

### 5. Support PCH
```python
with project("Engine"):
    pchheader("pch.h")
    pchsource("pch.cpp")
```

### 6. Location par Défaut
```python
with project("MyLib"):
    # location = "." par défaut
    location(".")              # Workspace dir
    location("libs/mylib")     # Relatif
    location("/abs/path")      # Absolu
```

## 🧪 Système de Tests Unitaires

### Intégration Automatique
- **Unitest** ajouté automatiquement au build
- Compilé en `staticlib` de manière transparente
- Aucune action requise de l'utilisateur

### Configuration Test
```python
with test("AppTests"):
    location(".")
    
    # Fichiers de tests
    testfiles(["tests/**.cpp"])
    
    # Exclure le main de l'app
    testmainfile("src/main.cpp")
    
    # Options CLI
    testoptions([
        "--verbose",
        "--parallel",
        "--filter=Math*",
        "--report=results.xml"
    ])
```

### Reporter Amélioré
Le reporter de tests affiche désormais :
- ✅ Emojis Unicode sur toutes plateformes
- 📊 Tableau formaté élégant
- 🎨 Couleurs ANSI + VT100
- 📍 Liens cliquables vers fichiers (VSCode, CLion, Xcode)
- ⚡ Barre de progression en temps réel

### Sortie Console
```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                       UNIT TEST FRAMEWORK - TEST REPORT                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝

  STATUS  TEST NAME                              ASSERTIONS    SUCCESS RATE    TIME
  ──────  ─────────────────────────────────────  ────────────  ─────────────  ───────
  ✓    Calculator::Addition                       4/4          100.0%         0.8ms
  ✓    Calculator::Subtraction                    3/3          100.0%         0.5ms
  ✗    Calculator::Division                       2/3           66.7%         1.2ms
         Failed assertions:
           1. Division by zero should throw
             Expected: exception of type std::invalid_argument
             Actual:   no exception thrown
             📍 tests/CalculatorTests.cpp:45 (Ctrl+click to open)

┌─────────────────────────────────── SUMMARY ───────────────────────────────────┐
│ Tests:        2 passed, 1 failed, 3 total                                     │
│ Assertions:   9 passed, 1 failed, 10 total                                    │
│ Success Rate: Tests: 66.7%, Assertions: 90.0%                                 │
│ Time:         2.5ms total, 0.8ms/test, 0.25ms/assert                         │
│ Performance:  1200 tests/sec, 4000 asserts/sec                               │
│ Result:       ❌ 1 TEST(S) FAILED                                             │
└───────────────────────────────────────────────────────────────────────────────┘
```

## 🚀 Performance

### Amélioration de Vitesse
- Premier build: 5.14s
- Build avec cache: **0.26s** (20x plus rapide)
- Compilation parallèle: Utilise tous les cores CPU

### Cache Intelligent
- Détection mtime + size (pas de hash complet)
- Invalidation automatique si fichier modifié
- Stockage JSON compact

## 📝 Migration depuis Nken

### 1. Renommer les Fichiers
```bash
mv myproject.nken myproject.jenga
mv nken.sh jenga.sh
mv nken.bat jenga.bat
```

### 2. Mettre à Jour les Scripts
```bash
# Avant
./nken.sh build

# Après
./jenga.sh build
```

### 3. Nettoyer le Cache
```bash
rm -rf .nken_cache
# Le nouveau cache .cjenga sera créé automatiquement
```

## 🎯 Fonctionnalités Complètes

### Affichage
- ✅ Logo JENGA magnifique
- ✅ Progrès temps réel `[1/5] Compiled: file.cpp`
- ✅ Erreurs formatées avec cadres et couleurs
- ✅ Auto-détection plateforme

### Performance
- ✅ Cache ultra-rapide (20x)
- ✅ Compilation parallèle
- ✅ Build incrémental intelligent

### Tests
- ✅ Auto-injection du main
- ✅ Reporter élégant avec emojis
- ✅ Liens cliquables vers code source
- ✅ Support multi-IDE (VSCode, CLion, Xcode, etc.)

### Configuration
- ✅ Extension `.jenga`
- ✅ Auto-commentaire des imports
- ✅ Cache `.cjenga/`
- ✅ Multi-plateforme

### IDE
- ✅ VSCode integration (`jenga gen`)
- ✅ IntelliSense complet
- ✅ Pas d'erreurs Pylance

## 📚 Documentation

- **README.md** - Guide principal
- **QUICKSTART.md** - Démarrage rapide
- **TESTING_GUIDE.md** - Guide des tests
- **CROSS_PLATFORM_GUIDE.md** - Multi-plateforme
- **ANDROID_EMSCRIPTEN_GUIDE.md** - Mobile/Web
- **ARCHITECTURE.md** - Architecture technique

## 🎉 Résumé

Jenga Build System est maintenant **100% opérationnel** avec :

1. ✅ Nouveau nom et logo
2. ✅ Extension `.jenga`
3. ✅ Cache `.cjenga/` optimisé
4. ✅ Compilation parallèle ultra-rapide
5. ✅ Tests unitaires intégrés
6. ✅ Reporter élégant avec emojis
7. ✅ Support PCH
8. ✅ Auto-commentaire des imports
9. ✅ Multi-plateforme (6 plateformes)
10. ✅ IDE integration complète

**Le système est prêt pour la production !** 🚀
