# 🏗️ LIVRE COMPLET JENGA BUILD SYSTEM

## 📚 Table des Matières

### Partie I : Introduction et Vue d'Ensemble
- [Chapitre 1 : Qu'est-ce que Jenga ?](#chapitre-1-qu-est-ce-que-jenga)
- [Chapitre 2 : Architecture du Système](#chapitre-2-architecture-du-système)
- [Chapitre 3 : Installation et Configuration](#chapitre-3-installation-et-configuration)

### Partie II : Guide Utilisateur
- [Chapitre 4 : Premiers Pas](#chapitre-4-premiers-pas)
- [Chapitre 5 : Commandes Principales](#chapitre-5-commandes-principales)
- [Chapitre 6 : Gestion des Projets](#chapitre-6-gestion-des-projets)
- [Chapitre 7 : Compilation et Build](#chapitre-7-compilation-et-build)
- [Chapitre 8 : Tests et Débogage](#chapitre-8-tests-et-débogage)

### Partie III : Guide Développeur
- [Chapitre 9 : Architecture Interne](#chapitre-9-architecture-interne)
- [Chapitre 10 : API et DSL](#chapitre-10-api-et-dsl)
- [Chapitre 11 : Système de Commandes](#chapitre-11-système-de-commandes)
- [Chapitre 12 : Gestion des Outils](#chapitre-12-gestion-des-outils)
- [Chapitre 13 : Extensibilité](#chapitre-13-extensibilité)

### Partie IV : Référence Avancée
- [Chapitre 14 : Configuration Avancée](#chapitre-14-configuration-avancée)
- [Chapitre 15 : Cross-Compilation](#chapitre-15-cross-compilation)
- [Chapitre 16 : Optimisations](#chapitre-16-optimisations)
- [Chapitre 17 : Dépannage](#chapitre-17-dépannage)

---

## Partie I : Introduction et Vue d'Ensemble

### Chapitre 1 : Qu'est-ce que Jenga ?

**Jenga** est un système de build moderne et multi-plateforme pour projets C/C++ utilisant un DSL (Domain Specific Language) unifié en Python. Conçu pour être rapide, flexible et facile à utiliser, Jenga offre une alternative moderne aux systèmes de build traditionnels comme CMake ou Make.

#### 🎯 Objectifs Principaux

1. **Simplicité d'utilisation** : Syntaxe Python intuitive pour la configuration
2. **Performance** : Compilation parallèle et cache intelligent pour des builds 20x plus rapides
3. **Multi-plateforme** : Support natif de Windows, Linux, macOS, Android, iOS et WebAssembly
4. **Intégration complète** : Testing, packaging, signature et déploiement intégrés
5. **Zéro dépendance** : Pure Python 3, aucun outil externe requis

#### 📊 Caractéristiques Clés

- **DSL Python unifié** pour la configuration des projets
- **Compilation parallèle** avec gestion automatique des dépendances
- **Cache intelligent** pour les builds incrémentaux
- **Framework de test intégré** (Unitest)
- **Outils de création intelligents** pour fichiers et projets
- **Support cross-compilation** (Android NDK, Emscripten)
- **Gestion des toolchains** multiples (GCC, Clang, MSVC)

### Chapitre 2 : Architecture du Système

#### 🏛️ Structure Hiérarchique

Jenga suit une architecture modulaire organisée autour de plusieurs composants clés :

```
Jenga/
├── jenga.py              # Point d'entrée principal
├── core/                 # Cœur du système
│   ├── api.py           # DSL et API de configuration
│   ├── buildsystem.py   # Moteur de compilation
│   ├── commands.py      # Registre des commandes
│   ├── loader.py        # Chargement des workspaces
│   └── variables.py     # Expansion des variables
├── Commands/            # Commandes implémentées
│   ├── build.py         # Commande de build
│   ├── create.py        # Création de projets/fichiers
│   ├── run.py          # Exécution des programmes
│   ├── test.py         # Tests unitaires
│   └── ...             # Autres commandes
└── utils/               # Utilitaires
    ├── display.py       # Affichage coloré
    └── reporter.py      # Rapports de build
```

#### 🔄 Flux de Travail Typique

1. **Configuration** : Définition du workspace et des projets via DSL Python
2. **Chargement** : Parsing et validation de la configuration
3. **Compilation** : Génération des commandes de compilation parallèle
4. **Liaison** : Création des exécutables/bibliothèques
5. **Test/Exécution** : Validation du résultat

### Chapitre 3 : Installation et Configuration

#### 📦 Installation

Jenga est un package Python pur qui peut être installé via pip ou utilisé directement depuis les sources :

```bash
# Depuis les sources
python -m pip install .

# Ou utilisation directe
./jenga.sh --version
jenga.bat --version
```

#### ⚙️ Configuration Système

Les scripts de lancement (`jenga.sh` et `jenga.bat`) détectent automatiquement :
- L'interpréteur Python disponible
- Le répertoire d'installation
- L'encodage UTF-8 pour l'affichage

#### 🔧 Prérequis

- **Python 3.7+** (aucune dépendance externe)
- **Compilateurs C/C++** selon la plateforme cible
- **Permissions d'écriture** pour les répertoires de build

---

## Partie II : Guide Utilisateur

### Chapitre 4 : Premiers Pas

#### 🚀 Création d'un Premier Projet

```bash
# Créer un workspace
jenga create workspace MonProjet
cd MonProjet

# Créer un projet C++
jenga create project MonApp --type consoleapp

# Créer un fichier source
jenga create file Main --type class

# Build et exécution
jenga build
jenga run
```

#### 📝 Structure d'un Workspace Jenga

Un workspace typique contient :

```
MonProjet/
├── workspace.jenga      # Configuration principale
├── Projects/
│   └── MonApp/
│       ├── MonApp.jenga # Configuration du projet
│       ├── src/
│       │   ├── Main.h
│       │   └── Main.cpp
│       └── Build/       # Généré automatiquement
└── Build/              # Artifacts de build
```

#### 📋 Fichier de Configuration Basique

```python
# workspace.jenga
with workspace("MonProjet"):
    configurations(["Debug", "Release"])
    platforms(["Windows", "Linux", "MacOS"])
    
    with project("MonApp"):
        consoleapp()
        language("C++")
        files(["src/*.cpp", "src/*.h"])
        targetdir("Build/Bin/%{cfg.buildcfg}")
```

### Chapitre 5 : Commandes Principales

#### 📜 Liste des Commandes Disponibles

| Commande | Description | Options Principales |
|----------|-------------|---------------------|
| `build` | Compile le workspace/projet | `--config`, `--platform`, `--project` |
| `rebuild` | Nettoie et rebuild | Mêmes options que build |
| `clean` | Nettoie les artefacts | `--project` |
| `run` | Exécute le programme | `--config`, `--debugger` |
| `test` | Lance les tests | `--config`, `--filter` |
| `create` | Crée éléments | `workspace`, `project`, `file` |
| `info` | Affiche les informations | Aucune |
| `package` | Package l'application | `--format` |
| `sign` | Signe l'application | `--keystore` |

#### 🎯 Exemples d'Utilisation

```bash
# Build spécifique
jenga build --config Release --platform Linux --project MonApp

# Build parallèle
jenga build --jobs 8

# Exécution avec debugger
jenga run --config Debug --debugger gdb

# Création avancée
jenga create file Player --type class --namespace Game
jenga create project Engine --type staticlib
```

### Chapitre 6 : Gestion des Projets

#### 🏗️ Types de Projets Supportés

Jenga supporte plusieurs types de projets :

- **ConsoleApp** : Application console
- **WindowedApp** : Application avec interface graphique
- **StaticLib** : Bibliothèque statique
- **SharedLib** : Bibliothèque partagée
- **TestSuite** : Suite de tests

#### 📁 Structure de Projet Avancée

```python
with project("GameEngine"):
    staticlib()
    language("C++")
    cppdialect("C++20")
    
    # Fichiers sources
    files([
        "src/**/*.cpp",
        "src/**/*.h",
        "include/**/*.h"
    ])
    
    # Exclusions
    excludefiles(["src/legacy/*.cpp"])
    
    # Répertoires d'inclusion
    includedirs(["include", "thirdparty/include"])
    
    # Précompiled headers
    pchheader("pch.h")
    pchsource("pch.cpp")
```

#### 🔗 Gestion des Dépendances

```python
with workspace("MonJeu"):
    with project("Engine"):
        staticlib()
        # ... configuration
    
    with project("Game"):
        consoleapp()
        links(["Engine"])  # Dépendance
        includedirs(["../Engine/include"])  # Headers
```

### Chapitre 7 : Compilation et Build

#### ⚡ Système de Compilation Parallèle

Jenga utilise un système de compilation parallèle intelligent :

- **Détection automatique** du nombre de cores CPU
- **Gestion des dépendances** entre fichiers
- **Cache incrémental** basé sur les timestamps
- **Reprise sur erreur** avec rapport détaillé

#### 🔧 Options de Build

```bash
# Build avec options avancées
jenga build \
    --config Release \
    --platform Windows \
    --toolchain msvc \
    --jobs 12 \
    --verbose \
    --no-cache
```

#### 📊 Rapports et Statistiques

Chaque build génère un rapport détaillé :

- Temps de compilation total
- Nombre de fichiers compilés
- Utilisation du cache
- Erreurs et avertissements
- Performance par thread

### Chapitre 8 : Tests et Débogage

#### 🧪 Framework de Test Intégré

Jenga inclut un framework de test complet :

```bash
# Lancer tous les tests
jenga test

# Tests avec filtrage
jenga test --filter "Math*"

# Tests avec debugger
jenga test --debugger gdb
```

#### 🔍 Débogage Avancé

Support de multiples debuggers :

- **GDB** : Debugger GNU (Linux/Windows)
- **LLDB** : Debugger LLVM (macOS/Linux)
- **Valgrind** : Analyse mémoire (Linux)

```bash
# Exécution avec GDB
jenga run --debugger gdb

# Exécution avec Valgrind
jenga run --debugger valgrind
```

#### 📝 Configuration des Tests

```python
with project("Tests"):
    testsuite()
    files(["tests/**/*.cpp"])
    links(["MainLibrary"])  # Lier à la bibliothèque testée
    
    # Options de test spécifiques
    testtimeout(30)  # Timeout de 30 secondes
    testfilter("*Test*")  # Filtre des tests
```

---

## Partie III : Guide Développeur

### Chapitre 9 : Architecture Interne

#### 🧩 Composants Principaux

1. **CommandRegistry** : Gestionnaire de commandes modulaire
2. **Compiler** : Moteur de compilation parallèle
3. **WorkspaceLoader** : Chargeur et validateur de configuration
4. **VariableExpander** : Système d'expansion de variables
5. **BuildCache** : Cache intelligent pour builds incrémentaux

#### 🔄 Cycle de Vie d'une Commande

```python
# 1. Parsing des arguments
args = parse_options(sys.argv[1:])

# 2. Chargement du workspace
workspace = load_workspace()

# 3. Exécution de la commande
registry.execute(command, options)

# 4. Génération du rapport
Reporter.generate_report()
```

#### 📦 Structure des Données

Les principales classes de données :

- **Workspace** : Conteneur de projets et configurations
- **Project** : Configuration d'un projet individuel
- **Toolchain** : Configuration du toolchain de compilation
- **CompilationUnit** : Unité de compilation individuelle

### Chapitre 10 : API et DSL

#### 🎨 Domain Specific Language (DSL)

Le DSL de Jenga utilise le contexte Python pour une syntaxe naturelle :

```python
with workspace("MonProjet"):
    configurations(["Debug", "Release"])
    
    with project("App"):
        consoleapp()
        language("C++")
        files(["src/*.cpp"])
```

#### 📋 API Complète

**Workspace API** :
- `configurations()` : Définit les configurations de build
- `platforms()` : Définit les plateformes supportées
- `project()` : Définit un nouveau projet

**Project API** :
- `consoleapp()` / `staticlib()` / etc. : Type de projet
- `language()` : Langage de programmation
- `files()` : Fichiers sources
- `links()` : Dépendances entre projets
- `includedirs()` : Répertoires d'inclusion

#### 🔧 Variables et Templates

Système de variables puissant :

```python
# Variables prédéfinies
targetdir("Build/Bin/%{cfg.buildcfg}/%{cfg.platform}")

# Variables personnalisées
define("VERSION_MAJOR", 1)
define("VERSION_MINOR", 0)
```

### Chapitre 11 : Système de Commandes

#### 🏗️ Architecture Modulaire

Chaque commande est un module indépendant :

```python
# Commands/build.py
def execute(options: dict) -> bool:
    workspace = load_workspace()
    compiler = Compiler(workspace, options)
    return compiler.build()
```

#### 🔄 Registre Automatique

Le CommandRegistry détecte automatiquement les commandes :

```python
class CommandRegistry:
    def _load_command_modules(self):
        for cmd_file in commands_dir.glob("*.py"):
            module = import_module(f"Commands.{module_name}")
            if hasattr(module, "execute"):
                self.commands[module_name] = module.execute
```

#### ✨ Commandes Personnalisées

Création d'une nouvelle commande :

```python
# Commands/custom.py
def execute(options: dict) -> bool:
    """Ma commande personnalisée"""
    # Implémentation ici
    return True
```

### Chapitre 12 : Gestion des Outils

#### 🔧 Support Multi-Toolchain

Jenga supporte nativement :
- **GCC** : Compilateur GNU
- **Clang** : Compilateur LLVM
- **MSVC** : Compilateur Microsoft
- **Android NDK** : Cross-compilation Android
- **Emscripten** : Compilation WebAssembly

#### 📐 Configuration des Toolchains

```python
# Configuration manuelle
toolchain("custom-gcc", {
    "compiler": "gcc",
    "cflags": ["-O2", "-Wall"],
    "cxxflags": ["-std=c++17"]
})
```

#### 🔄 Détection Automatique

Le système détecte automatiquement :
- Les compilateurs disponibles
- Les versions et capacités
- Les chemins d'installation

### Chapitre 13 : Extensibilité

#### 🔌 Plugins et Extensions

Jenga est conçu pour être extensible :

**Extensions de Commandes** :
```python
# Nouvelle commande dans Commands/
def execute(options):
    # Implémentation
    pass
```

**Extensions d'API** :
```python
# Nouvelle fonction dans core/api.py
def custom_function(value):
    """Extension de l'API"""
    # Implémentation
```

#### 🎯 Points d'Extension

1. **Nouvelles Commandes** : Ajout de fonctionnalités
2. **Nouveaux Toolchains** : Support de nouveaux compilateurs
3. **Nouvelles Plateformes** : Support de nouvelles cibles
4. **Systèmes de Build** : Intégration avec d'autres outils

---

## Partie IV : Référence Avancée

### Chapitre 14 : Configuration Avancée

#### ⚙️ Optimisations de Compilation

```python
with project("PerformanceCritical"):
    optimization("Full")
    
    # Flags spécifiques
    cflags(["-O3", "-march=native"])
    cxxflags(["-std=c++20", "-fopenmp"])
    
    # Définitions de préprocesseur
    defines(["NDEBUG", "USE_SIMD"])
```

#### 🔧 Configuration Cross-Platform

```python
# Configuration conditionnelle par plateforme
if platform == "Windows":
    defines(["WIN32", "_WINDOWS"])
    links(["user32", "gdi32"])
elif platform == "Linux":
    defines(["LINUX"])
    links(["pthread", "dl"])
```

### Chapitre 15 : Cross-Compilation

#### 🤖 Compilation Android

```python
# Configuration Android
toolchain("android", {
    "compiler": "clang",
    "sysroot": "${ANDROID_NDK}/sysroot",
    "targettriple": "aarch64-linux-android21"
})

with project("AndroidApp"):
    windowedapp()
    platform("Android")
    toolchain("android")
```

#### 🌐 Compilation WebAssembly

```python
# Configuration Emscripten
toolchain("emscripten", {
    "compiler": "emcc",
    "cflags": ["-s WASM=1"],
    "ldflags": ["-s ALLOW_MEMORY_GROWTH=1"]
})
```

### Chapitre 16 : Optimisations

#### 🚀 Performance du Build System

**Cache Intelligent** :
- Basé sur les timestamps des fichiers
- Validation par hash SHA256 optionnelle
- Persistance entre les sessions

**Compilation Parallèle** :
- Utilisation maximale des cores CPU
- Gestion automatique des dépendances
- Limitation configurable des jobs

#### 📊 Métriques et Monitoring

Jenga fournit des métriques détaillées :
- Temps de compilation par fichier
- Utilisation du cache
- Performance des threads
- Analyse des goulots d'étranglement

### Chapitre 17 : Dépannage

#### 🔍 Diagnostic des Problèmes

**Commandes de diagnostic** :
```bash
# Informations détaillées
jenga info --verbose

# Validation de la configuration
jenga diagnose

# Nettoyage complet
jenga clean --all
```

#### 🐛 Résolution d'Erreurs Courantes

**Problèmes de Configuration** :
- Vérifier les chemins des fichiers
- Valider les dépendances entre projets
- Confirmer la disponibilité des toolchains

**Problèmes de Compilation** :
- Vérifier les droits d'accès
- Confirmer l'installation des compilateurs
- Examiner les logs détaillés avec `--verbose`

---

## 📖 Conclusion

Jenga représente une approche moderne et efficace pour la construction de projets C/C++. En combinant la simplicité d'un DSL Python avec la puissance d'un système de build professionnel, il offre une alternative convaincante aux outils traditionnels.

### 🎯 Points Forts

1. **Productivité** : Configuration rapide et intuitive
2. **Performance** : Builds parallèles et cache intelligent
3. **Flexibilité** : Support multi-plateforme étendu
4. **Intégration** : Toolchain complet de développement

### 🔮 Évolutions Futures

Le système est conçu pour évoluer avec :
- Support de nouveaux langages
- Intégration avec d'autres écosystèmes
- Améliorations continues des performances

### 📚 Ressources Complémentaires

- Documentation complète dans le dossier `Docs/`
- Exemples de projets dans le repository
- Guide de migration depuis d'autres systèmes de build

---

*Ce livre a été généré automatiquement à partir de l'analyse du code source de Jenga Build System v1.0.3*  
*Copyright © 2024-2026 Rihen - Tous droits réservés*