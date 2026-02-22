# Guide d'Accélération de la Compilation - Jenga

**Date**: 22 février 2026
**Objectif**: Compiler aussi vite que Visual Studio, CLion, CodeBlocks

---

## 🎯 Techniques Utilisées par les IDE Professionnels

### 1. **Compilation Parallèle** ✅ DÉJÀ IMPLÉMENTÉ

**Ce que font les IDE** :
- Visual Studio : `/MP` (multi-process compilation)
- CLion/Make : `-j<N>` (N = nombre de cores CPU)
- CodeBlocks : Parallel builds settings

**Comment Jenga le fait** :
```python
# Dans Builder.py, compilation parallèle native
num_jobs = os.cpu_count() or 4
args.append(f"-j{num_jobs}")
```

**Impact** : **2-8x plus rapide** sur machines multi-core (4-16 cores)

---

### 2. **Cache de Compilation (ccache/sccache)** ⚠️ À IMPLÉMENTER

**Ce que font les IDE** :
- Visual Studio : Build cache intégré
- CLion : Supporte ccache/sccache via CMake
- Xcode : Clang module cache

**Principe** :
- Stocke les fichiers `.o` compilés dans un cache global basé sur le hash du code source
- Si le même `.cpp` est compilé 2x avec les mêmes flags → réutilise le `.o` existant
- Cache partagé entre projets et machines (réseau)

**Implémentation pour Jenga** :
```python
# Option 1: Wrapper ccache (Linux/macOS)
if shutil.which("ccache"):
    compiler = f"ccache {compiler}"

# Option 2: sccache (multi-plateforme, Rust)
if shutil.which("sccache"):
    os.environ["RUSTC_WRAPPER"] = "sccache"
    compiler = f"sccache {compiler}"
```

**Installation utilisateur** :
```bash
# Linux/macOS
sudo apt install ccache       # Ubuntu
brew install ccache           # macOS

# Windows/Linux/macOS (sccache - plus moderne)
cargo install sccache
# ou télécharger binaire: https://github.com/mozilla/sccache
```

**Configuration Jenga** :
```python
# Dans JengaConfig.py, ajouter:
class JengaConfig:
    use_ccache: bool = True  # Auto-détecte ccache/sccache
    ccache_dir: Optional[str] = None  # ~/.ccache par défaut
```

**Impact** : **10-100x plus rapide** pour recompilations (après clean par exemple)

---

### 3. **Precompiled Headers (PCH)** 🔥 HAUTE PRIORITÉ

**Ce que font les IDE** :
- Visual Studio : `/Yc` (create PCH), `/Yu` (use PCH)
- GCC/Clang : `-include-pch`
- Xcode : Automatic precompiled headers

**Principe** :
- Headers lourds (`<iostream>`, `<vector>`, STL, Qt, Boost) compilés 1x → `.pch` binaire
- Tous les `.cpp` réutilisent ce `.pch` sans reparser/recompiler les headers
- Parsing de `<iostream>` : **~200ms** → avec PCH : **~5ms**

**Implémentation pour Jenga** :

**Syntaxe DSL** :
```python
with project("MyApp"):
    files(["src/**.cpp"])
    pch("src/pch.h")  # Nouveau: fichier precompiled header
    # Ou auto-détection:
    autopch(True)     # Crée automatiquement pch.h avec tous les includes communs
```

**Génération automatique** :
```python
# Analyser tous les .cpp pour trouver les headers communs (>50% des fichiers)
common_headers = [
    "<iostream>", "<vector>", "<string>",
    "<memory>", "<algorithm>", "<map>"
]
# Générer src/pch.h:
with open("src/pch.h", "w") as f:
    f.write("// Auto-generated PCH\n")
    for h in common_headers:
        f.write(f"#include {h}\n")
```

**Compilation** :
```bash
# 1. Compiler le PCH (1x seulement)
clang++ -x c++-header src/pch.h -o Build/pch.h.pch

# 2. Compiler chaque .cpp avec le PCH
clang++ -include-pch Build/pch.h.pch src/main.cpp -o main.o
```

**Impact** : **1.5-3x plus rapide** pour projets avec beaucoup de headers STL/Boost/Qt

---

### 4. **Unity Builds (Jumbo/Amalgamation)** 🚀 TRÈS EFFICACE

**Ce que font les IDE** :
- Visual Studio : "Amalgamated builds" (Unreal Engine style)
- CMake : `UNITY_BUILD` option
- Chromium/V8 : Jumbo builds

**Principe** :
- Combiner plusieurs `.cpp` en un seul mega `.cpp`
- Au lieu de compiler 100 fichiers → compile 10 mega-fichiers de 10 `.cpp` chacun
- Réduit drastiquement le parsing de headers (fait 1x au lieu de 100x)

**Exemple Unity Build** :
```cpp
// Build/Unity_0.cpp (auto-généré)
#include "src/file1.cpp"
#include "src/file2.cpp"
#include "src/file3.cpp"
// ... 10 fichiers max par unity
```

**Implémentation pour Jenga** :
```python
# DSL:
with project("MyApp"):
    files(["src/**.cpp"])
    unitybuild(True, files_per_unity=10)  # Groupe par 10
```

**Génération automatique** :
```python
def GenerateUnityBuilds(project, files_per_unity=10):
    cpp_files = [f for f in project.files if f.endswith('.cpp')]
    unity_dir = Path("Build") / "Unity"
    unity_dir.mkdir(exist_ok=True)

    unity_files = []
    for i, chunk in enumerate(chunks(cpp_files, files_per_unity)):
        unity_file = unity_dir / f"Unity_{i}.cpp"
        with open(unity_file, "w") as f:
            for cpp in chunk:
                f.write(f'#include "{Path(cpp).resolve()}"\n')
        unity_files.append(unity_file)

    return unity_files  # Compile ces fichiers au lieu des .cpp originaux
```

**Avantages** :
- **3-10x plus rapide** compilation
- Moins d'overhead de linker (moins de `.o` files)

**Inconvénients** :
- Problèmes de symboles si fichiers ont des `static` variables de même nom
- Debug plus complexe (stack traces pointent vers Unity_X.cpp)
- Pas idéal pour développement actif (recompile 10 fichiers si 1 change)

**Stratégie hybride** :
```python
# Mode Debug: compilation normale (itération rapide)
if config == "Debug":
    unitybuild(False)
# Mode Release: unity builds (build from scratch rapide)
elif config == "Release":
    unitybuild(True, files_per_unity=15)
```

---

### 5. **Modules C++20** 🆕 FUTUR (déjà un exemple dans Jenga!)

**Ce que font les IDE** :
- Visual Studio 2022 : Support complet modules C++20
- Clang 16+ : `-std=c++20 -fmodules`

**Principe** :
- Remplace `#include` par `import`
- Headers compilés 1x en **BMI** (Binary Module Interface)
- Plus besoin de guards `#ifndef`, parsing instantané

**Exemple** :
```cpp
// math.cppm (module interface)
export module math;
export int add(int a, int b) { return a + b; }

// main.cpp
import math;  // Au lieu de #include "math.h"
int main() { return add(1, 2); }
```

**Impact** : **5-20x plus rapide** que headers classiques (parsing quasi-instantané)

**Note** : Jenga a déjà **Exemple 10 - Modules C++20** ! À tester et documenter.

---

### 6. **Compilation Distribuée** 🌐 OPTIONNEL (grandes équipes)

**Ce que font les IDE** :
- Visual Studio : IncrediBuild (distribué sur réseau)
- CLion : distcc/icecc
- Unreal Engine : FASTBuild

**Principe** :
- Distribuer la compilation de chaque `.cpp` sur N machines du réseau
- Build farm : 100 cores répartis sur 10 machines

**Implémentation** :
```bash
# Linux: distcc (distributed compiler)
sudo apt install distcc
# Configurer réseau de machines
export DISTCC_HOSTS="localhost/4 192.168.1.100/8 192.168.1.101/8"
CC="distcc gcc" jenga build
```

**Impact** : **Linear scaling** avec nombre de machines (10 machines = 10x plus rapide)

**Complexité** : Haute (setup réseau, sécurité, versions compilateurs identiques)

---

### 7. **Link-Time Optimization (LTO)** ⚡ DÉJÀ POSSIBLE

**Ce que font les IDE** :
- Visual Studio : `/LTCG` (Link-Time Code Generation)
- GCC/Clang : `-flto`

**Principe** :
- Optimisations inter-fichiers au moment du link (inlining entre `.cpp`)
- Plus lent à compiler mais exécutable plus rapide

**Jenga DSL** :
```python
with project("MyApp"):
    optimize(Optimization.FULL)
    lto(True)  # Link-Time Optimization
```

**Flags compilateur** :
```bash
# Compilation
clang++ -flto -c src/*.cpp
# Link
clang++ -flto src/*.o -o app  # Fait l'optimisation globale ici
```

**Impact** :
- Compilation : **+20-50% plus lente**
- Exécution : **+10-30% plus rapide**

---

### 8. **Dépendances Intelligentes** ✅ DÉJÀ IMPLÉMENTÉ

**Ce que font les IDE** :
- Ninja : Graphe de dépendances optimal
- Make : Fichiers `.d` avec dépendances

**Comment Jenga le fait** :
```python
# Builder.py:681 - _NeedsCompileSource()
# Vérifie:
# 1. .o existe?
# 2. source.cpp plus récent que .o?
# 3. Fichier .d (dépendances) existe?
# 4. Headers inclus plus récents que .o?
# 5. Signature de compilation changée?
```

**Génération des dépendances** :
```bash
# GCC/Clang génère automatiquement les .d files
clang++ -MMD -MF main.d -c main.cpp -o main.o
# main.d contient: main.o: main.cpp header1.h header2.h ...
```

**Impact** : Évite recompilations inutiles (déjà optimal dans Jenga)

---

## 📊 Comparaison des Techniques

| Technique | Gain de vitesse | Complexité | Priorité | Statut Jenga |
|-----------|----------------|------------|----------|--------------|
| **Compilation parallèle** | 2-8x | Faible | ✅ Haute | ✅ Implémenté |
| **ccache/sccache** | 10-100x (rebuild) | Faible | ✅ Haute | ⚠️ À implémenter |
| **Precompiled Headers** | 1.5-3x | Moyenne | ✅ Haute | ⚠️ À implémenter |
| **Unity Builds** | 3-10x | Moyenne | 🔶 Moyenne | ⚠️ À implémenter |
| **Modules C++20** | 5-20x | Haute | 🔶 Moyenne | ✅ Exemple existe |
| **Compilation distribuée** | Nx machines | Très haute | 🔻 Faible | ❌ Non pertinent |
| **LTO** | +20% runtime | Faible | 🔶 Moyenne | ✅ Possible |
| **Dépendances intelligentes** | Évite inutiles | Faible | ✅ Haute | ✅ Implémenté |

---

## 🚀 Plan d'Implémentation Recommandé

### Phase 1 : Quick Wins (1-2 heures)

1. **ccache/sccache** :
   ```python
   # Dans Builder.py, détecter et wrapper le compilateur
   def _GetCompilerCommand(self):
       compiler = str(self.toolchain.cxxPath)
       if self.config.use_ccache:
           if shutil.which("sccache"):
               return f"sccache {compiler}"
           elif shutil.which("ccache"):
               return f"ccache {compiler}"
       return compiler
   ```

2. **Documentation utilisateur** :
   ```markdown
   # Accélérer les builds Jenga

   ## Installer ccache (Linux/macOS)
   sudo apt install ccache

   ## Installer sccache (Windows/Linux/macOS)
   # Télécharger: https://github.com/mozilla/sccache/releases
   # Ou compiler:
   cargo install sccache

   ## Utilisation automatique
   jenga build  # Détecte automatiquement ccache/sccache
   ```

### Phase 2 : Precompiled Headers (4-6 heures)

1. **Auto-détection headers communs** :
   ```python
   def DetectCommonHeaders(project):
       from collections import Counter
       headers = Counter()
       for cpp_file in project.files:
           with open(cpp_file) as f:
               for line in f:
                   if line.startswith("#include"):
                       headers[line.strip()] += 1
       # Garder headers présents dans >50% des fichiers
       threshold = len(project.files) * 0.5
       return [h for h, count in headers.items() if count >= threshold]
   ```

2. **DSL API** :
   ```python
   pch("src/pch.h")           # Manuel
   autopch(True)              # Auto-généré
   pchthreshold(0.5)          # 50% des fichiers minimum
   ```

### Phase 3 : Unity Builds (3-4 heures)

1. **Génération automatique** :
   ```python
   def GenerateUnityBuilds(project, config):
       if config == "Debug":
           return project.files  # Mode normal en debug

       cpp_files = [f for f in project.files if f.endswith('.cpp')]
       return CreateUnityFiles(cpp_files, files_per_unity=10)
   ```

2. **DSL API** :
   ```python
   unitybuild(True)                    # Activé/désactivé
   unitysize(10)                       # Fichiers par unity
   unityconfigs(["Release", "Ship"])   # Seulement certaines configs
   ```

---

## 💡 Techniques Avancées (Optionnel)

### Incremental Linking (MSVC)
```bash
# Windows: Link incrémental (plus rapide mais .exe plus gros)
link /INCREMENTAL main.obj libs.lib
```

### Thin LTO (Clang)
```bash
# LTO plus rapide que full LTO
clang++ -flto=thin -c src/*.cpp
```

### Response Files (Windows)
```bash
# Éviter dépassement ligne de commande (>8191 chars Windows)
echo main.obj lib.obj > objects.rsp
link @objects.rsp
```

---

## 📈 Résultats Attendus

### Projet Typique (100 fichiers .cpp, STL)

| Configuration | Temps (avant) | Temps (après) | Gain |
|--------------|---------------|---------------|------|
| **Clean build** | 120s | 15s | **8x** |
| **Rebuild (ccache)** | 120s | 2s | **60x** |
| **Incremental (1 fichier)** | 3s | 1s | **3x** |
| **Unity build** | 120s | 25s | **4.8x** |
| **PCH + ccache + unity** | 120s | **5s** | **24x** 🚀 |

### Projet Énorme (1000 fichiers, Unreal/Chromium style)

| Configuration | Temps (avant) | Temps (après) | Gain |
|--------------|---------------|---------------|------|
| **Clean build** | 45min | 4min | **11x** |
| **Rebuild (ccache + distcc 10 machines)** | 45min | 15s | **180x** |
| **Unity + PCH + LTO** | 45min | 6min | **7.5x** |

---

## ✅ Checklist d'Implémentation

- [x] **Compilation parallèle** (`-j`) - DÉJÀ FAIT
- [x] **Cache timestamp** (_NeedsCompileSource) - DÉJÀ FAIT
- [ ] **ccache/sccache auto-détection**
- [ ] **Precompiled Headers (PCH)**
  - [ ] DSL API: `pch()`, `autopch()`
  - [ ] Détection headers communs
  - [ ] Compilation PCH automatique
  - [ ] Utilisation PCH dans builds
- [ ] **Unity Builds**
  - [ ] DSL API: `unitybuild()`, `unitysize()`
  - [ ] Génération fichiers Unity_X.cpp
  - [ ] Mode hybride Debug/Release
- [ ] **C++20 Modules**
  - [ ] Tester Exemple 10
  - [ ] Documenter workflow
  - [ ] Support multi-plateforme
- [ ] **LTO configurablepar DSL**
- [ ] **Documentation utilisateur complète**
- [ ] **Benchmarks avant/après**

---

## 🎓 Ressources

- **ccache**: https://ccache.dev/
- **sccache**: https://github.com/mozilla/sccache
- **CMake Unity Builds**: https://cmake.org/cmake/help/latest/prop_tgt/UNITY_BUILD.html
- **C++20 Modules**: https://en.cppreference.com/w/cpp/language/modules
- **Chromium Jumbo Builds**: https://chromium.googlesource.com/chromium/src/+/main/docs/jumbo.md
- **Unreal Build Tool**: https://docs.unrealengine.com/en-US/ProductionPipelines/BuildTools/UnrealBuildTool/

---

**Conclusion** : Avec ccache + PCH + Unity builds, Jenga peut compiler **10-30x plus vite** que la version actuelle, rivalisant avec Visual Studio et CLion! 🚀
