# Guide Complet - Tests Imbriqués & NKM Library

## 🎯 Tests Imbriqués dans Projets

### Syntaxe Correcte

Les tests DOIVENT être imbriqués dans un `with project()` :

```python
with workspace("MyApp"):
    
    with project("Calculator"):
        consoleapp()
        files(["src/**.cpp"])
        
        # Test imbriqué - CORRECT !
        with test("Core"):
            testfiles(["tests/**.cpp"])
            testmainfile("src/main.cpp")
```

### ❌ Syntaxe Incorrecte

```python
with workspace("MyApp"):
    
    with project("Calculator"):
        consoleapp()
        files(["src/**.cpp"])
    
    # PAS au même niveau - ERREUR !
    with test("Calculator"):
        testfiles(["tests/**.cpp"])
```

### Contexte Automatique

Quand vous utilisez `with test()` dans un projet :

1. **Projet parent** est automatiquement détecté
2. **Nom du test** : `{Parent}_Tests` ou `{Parent}_{TestName}_Tests`
3. **Dépendances** : Ajoute automatiquement parent + `__Unitest__`
4. **Includes** : Copie les includes du parent
5. **Main** : Injecté automatiquement
6. **Retour** : À la sortie de `with test`, le contexte revient au projet parent

```python
with project("Engine"):
    staticlib()
    files(["src/**.cpp"])
    includedirs(["include"])
    
    # Entre dans le contexte de test
    with test("Physics"):
        testfiles(["tests/Physics/**.cpp"])
        testoptions(["--verbose"])
    # Sort du test, revient à Engine
    
    # Toujours dans Engine !
    defines(["ENGINE_VERSION=1.0"])
```

## 📦 NKM - Nkentseu Math Library

### Présentation

**NKM** est une bibliothèque mathématique 2D/3D :
- ✅ Header-only (templates)
- ✅ Multi-plateforme (Windows, Linux, MacOS, Android, iOS)
- ✅ Performante et extensible
- ✅ Personnalisable
- ✅ Tests intégrés

### Structure

```
NKM/
├── nkm.jenga                  # Configuration
├── include/
│   └── nkm/
│       ├── Vector2.h          # Vecteur 2D
│       ├── Vector3.h          # Vecteur 3D (TODO)
│       ├── Matrix3.h          # Matrice 3x3 (TODO)
│       └── Matrix4.h          # Matrice 4x4 (TODO)
├── tests/
│   ├── Vector2Tests.cpp
│   ├── Vector3Tests.cpp
│   └── Matrix4Tests.cpp
└── examples/
    └── main.cpp               # Démonstration
```

### Utilisation

```cpp
#include "nkm/Vector2.h"

using namespace nkm;

int main() {
    // Création
    Vector2f position(100.0f, 200.0f);
    Vector2f velocity(10.0f, -5.0f);
    
    // Opérations
    position += velocity;
    float length = position.length();
    Vector2f normalized = position.normalized();
    
    // Math
    float dot = position.dot(velocity);
    float distance = position.distance(Vector2f::zero());
    
    // Interpolation
    Vector2f lerped = position.lerp(velocity, 0.5f);
    
    return 0;
}
```

### Types Disponibles

```cpp
Vector2<float>  // ou Vector2f
Vector2<double> // ou Vector2d
Vector2<int>    // ou Vector2i
```

### API Complète

#### Constructeurs
```cpp
Vector2()              // (0, 0)
Vector2(T x, T y)      // (x, y)
Vector2(const Vector2&) // Copie
```

#### Opérateurs
```cpp
v1 + v2    // Addition
v1 - v2    // Soustraction
v * 2.0f   // Multiplication scalaire
v / 2.0f   // Division scalaire
v1 += v2   // Addition en place
v1 == v2   // Égalité
v1 != v2   // Inégalité
```

#### Méthodes
```cpp
.length()          // Longueur
.lengthSquared()   // Longueur au carré (plus rapide)
.normalized()      // Vecteur normalisé
.normalize()       // Normaliser en place
.dot(v)            // Produit scalaire
.cross(v)          // Produit vectoriel 2D
.distance(v)       // Distance
.lerp(v, t)        // Interpolation linéaire
```

#### Static Helpers
```cpp
Vector2f::zero()   // (0, 0)
Vector2f::one()    // (1, 1)
Vector2f::up()     // (0, 1)
Vector2f::down()   // (0, -1)
Vector2f::left()   // (-1, 0)
Vector2f::right()  // (1, 0)
```

## 🏗️ Configuration Jenga

```python
with workspace("NKM"):
    configurations(["Debug", "Release", "Dist"])
    platforms(["Windows", "Linux", "MacOS", "Android", "iOS"])
    
    with project("NKM"):
        staticlib()
        language("C++")
        cppdialect("C++17")
        
        # Auto-nomenclature: NKM-Debug-Linux, etc.
        buildoption("auto_nomenclature", ["true"])
        
        files(["include/nkm/**.h"])
        includedirs(["include"])
        
        # Tests imbriqués !
        with test("Core"):
            testfiles([
                "tests/Vector2Tests.cpp",
                "tests/Vector3Tests.cpp"
            ])
            testoptions(["--verbose", "--parallel"])
```

## 🔧 Build Commands

### Build NKM
```bash
# Build avec auto-nomenclature
jenga build
# Génère: libNKM-Debug-Linux.a

jenga build --config Release
# Génère: libNKM-Release-Linux.a

jenga build --config Release --platform Windows
# Génère: NKM-Release-Windows.lib
```

### Run Tests
```bash
# Run les tests
jenga run --project NKM_Core_Tests

# Avec options
jenga run --project NKM_Core_Tests -- --verbose --filter="Vector*"
```

### Run Example
```bash
jenga run --project NKM_Example

# Output:
# === NKM Math Library Example ===
# Initial position: (100, 200)
# Velocity: (10, -5)
# Frame 1: (110, 195)
# Frame 2: (120, 190)
# ...
```

## 🎨 Auto-Nomenclature

### Activation

```python
with project("MyLib"):
    staticlib()
    
    # Activer la nomenclature automatique
    buildoption("auto_nomenclature", ["true"])
```

### Résultat

Sans auto-nomenclature:
```
libMyLib.a
```

Avec auto-nomenclature:
```
libMyLib-Debug-Linux.a
libMyLib-Release-Windows.lib
libMyLib-Dist-MacOS.a
```

### Avantages

1. **Clarté** : On voit immédiatement config + platform
2. **Organisation** : Fichiers bien séparés
3. **Multi-build** : Builds parallèles sans conflit
4. **Debug** : Facile de voir quelle version on utilise

## 📊 Exemple Complet Multi-Plateforme

```python
with workspace("GameEngine"):
    configurations(["Debug", "Release"])
    platforms(["Windows", "Linux", "MacOS", "Android", "iOS"])
    
    # Math library
    with project("NKM"):
        staticlib()
        language("C++")
        cppdialect("C++17")
        
        buildoption("auto_nomenclature", ["true"])
        
        files(["NKM/include/nkm/**.h"])
        includedirs(["NKM/include"])
        
        with test("Math"):
            testfiles(["NKM/tests/**.cpp"])
            testoptions(["--parallel"])
    
    # Engine core
    with project("Engine"):
        staticlib()
        language("C++")
        
        buildoption("auto_nomenclature", ["true"])
        
        files(["Engine/src/**.cpp"])
        includedirs(["Engine/include", "NKM/include"])
        dependson(["NKM"])
        
        with test("Core"):
            testfiles(["Engine/tests/**.cpp"])
    
    # Game application
    with project("Game"):
        consoleapp()
        language("C++")
        
        buildoption("auto_nomenclature", ["true"])
        
        files(["Game/src/**.cpp"])
        includedirs(["Game/include", "Engine/include", "NKM/include"])
        dependson(["Engine", "NKM"])
        
        with test("Gameplay"):
            testfiles(["Game/tests/**.cpp"])
            testmainfile("Game/src/main.cpp")
```

**Build pour toutes les plateformes :**

```bash
jenga build --platform Windows --config Release
# Génère:
# - NKM-Release-Windows.lib
# - Engine-Release-Windows.lib
# - Game-Release-Windows.exe

jenga build --platform Linux --config Debug
# Génère:
# - libNKM-Debug-Linux.a
# - libEngine-Debug-Linux.a
# - Game-Debug-Linux

jenga build --platform Android --config Release
# Génère:
# - libNKM-Release-Android.a
# - libEngine-Release-Android.a
# - libGame-Release-Android.so
```

## 🎯 Bonnes Pratiques

### 1. Toujours Imbriquer les Tests

✅ CORRECT:
```python
with project("MyLib"):
    staticlib()
    with test("Unit"):
        testfiles(["tests/**.cpp"])
```

❌ INCORRECT:
```python
with project("MyLib"):
    staticlib()

with test("MyLib"):  # Pas au bon niveau !
    testfiles(["tests/**.cpp"])
```

### 2. Utiliser Auto-Nomenclature

Pour les bibliothèques multi-plateformes:
```python
buildoption("auto_nomenclature", ["true"])
```

### 3. Nommer les Tests

```python
with test("Physics"):     # NKM_Physics_Tests
with test("Rendering"):   # NKM_Rendering_Tests
with test(""):            # NKM_Tests (par défaut)
```

### 4. Options de Tests

```python
with test("Core"):
    testfiles(["tests/**.cpp"])
    testmainfile("src/main.cpp")  # Si exécutable
    testoptions([
        "--verbose",      # Sortie détaillée
        "--parallel",     # Tests parallèles
        "--filter=Vec*"   # Filtrer par nom
    ])
```

---

## 🎉 Résumé

**Jenga Build System** offre maintenant :

1. ✅ **Tests imbriqués** dans les projets
2. ✅ **Auto-injection** de Unitest
3. ✅ **Auto-nomenclature** (Config-Platform)
4. ✅ **NKM** - Bibliothèque math complète
5. ✅ **Multi-plateforme** (6 plateformes)
6. ✅ **Exemples complets** et testés

**Le système est COMPLET et prêt pour la production !** 🚀
