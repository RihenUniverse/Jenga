# 21_zig_cross_compile

## Description

Exemple démontrant la **cross-compilation** d'un programme C++ pour Linux depuis Windows en utilisant le compilateur **Zig** comme toolchain.

Zig fournit une toolchain C/C++ complète et portable qui permet de compiler pour différentes plateformes sans avoir besoin d'installer des SDK natifs complexes. Cet exemple montre comment :

- Définir un toolchain personnalisé Zig dans Jenga
- Compiler un binaire Linux ELF depuis Windows
- Utiliser la STL (Standard Template Library) en cross-compilation
- Configurer les target triples et flags de compilation

C'est une solution idéale pour du build multi-plateformes dans des environnements CI/CD.

## Plateformes supportées

- **Source** : Windows (développement)
- **Target** : Linux x86_64 GNU (binaire généré)

## Prérequis

### Installation de Zig

1. Télécharger Zig depuis [https://ziglang.org/download/](https://ziglang.org/download/)
2. Extraire dans `C:\Zig\` (ou ajuster les chemins dans le .jenga)
3. Ajouter au PATH (optionnel)

### Scripts Wrapper

Le projet utilise des scripts batch pour wrapper les commandes Zig :
- `zig-cc.bat` : Wrapper pour le compilateur C
- `zig-c++.bat` : Wrapper pour le compilateur C++
- Ces scripts doivent être dans `E:\Projets\Closed\Jenga\scripts\` (ou ajuster le chemin)

## Architecture

```
21_zig_cross_compile/
├── 21_zig_cross_compile.jenga    # Configuration Jenga avec toolchain Zig
└── src/
    └── main.cpp                   # Programme de test C++ (STL + récursion)
```

## Fichiers

### main.cpp

Programme C++ démontrant :
- **STL** : `std::vector`, `std::sort`, `std::cout`
- **Algorithmes** : Tri et itération
- **Récursion** : Calcul de Fibonacci
- **Affichage** : Sortie formatée console

### 21_zig_cross_compile.jenga

Configuration complète du toolchain Zig :
- **Target OS** : Linux
- **Target Arch** : x86_64
- **Target Triple** : `x86_64-linux-gnu`
- **Toolchain personnalisé** : "zig-linux-x64"
- **Compilateurs** : Scripts wrapper zig-cc/zig-c++
- **Flags** : `-target x86_64-linux-gnu`, `-std=c++17`

## Compilation

### Build depuis Windows pour Linux

```bash
jenga build --config Debug
jenga build --config Release
```

Le binaire généré sera un ELF Linux x86_64, **non exécutable sur Windows**.

### Vérifier le binaire généré

Sur Windows avec WSL ou Git Bash :
```bash
file Build/Bin/Debug-Linux/ZigCrossApp/ZigCrossApp
# Sortie attendue : ELF 64-bit LSB executable, x86-64, version 1 (SYSV)
```

## Exécution

Le binaire doit être exécuté sur une machine Linux ou dans WSL :

```bash
# Depuis WSL (Windows Subsystem for Linux)
./Build/Bin/Debug-Linux/ZigCrossApp/ZigCrossApp

# Depuis une machine Linux native
./ZigCrossApp
```

## Sortie attendue

```
==================================
Cross-compiled with Zig!
==================================

Sorted numbers: 1 2 3 4 5 6 7 8 9

Fibonacci sequence (first 10):
F(0) = 0
F(1) = 1
F(2) = 1
F(3) = 2
F(4) = 3
F(5) = 5
F(6) = 8
F(7) = 13
F(8) = 21
F(9) = 34

==================================
All tests passed!
==================================
```

## Points clés

- **Cross-compilation sans SDK** : Pas besoin d'installer un SDK Linux complet sur Windows
- **Toolchain portable** : Zig embarque libc et libstdc++ pour toutes les plateformes
- **Target triple** : `x86_64-linux-gnu` spécifie précisément la plateforme cible
- **C++ standard** : Support complet C++17 avec STL
- **Binaire natif** : Le résultat est un vrai binaire Linux ELF (pas d'émulation)

## Configuration du Toolchain Zig

Le fichier `.jenga` définit un toolchain personnalisé :

```python
with toolchain("zig-linux-x64", "clang"):
    settarget("Linux", "x86_64", "gnu")
    targettriple("x86_64-linux-gnu")
    ccompiler(r"E:\Projets\Closed\Jenga\scripts\zig-cc.bat")
    cppcompiler(r"E:\Projets\Closed\Jenga\scripts\zig-c++.bat")
    linker(r"E:\Projets\Closed\Jenga\scripts\zig-c++.bat")
    archiver(r"C:\Zig\zig-x86_64-windows-0.16.0\zig.exe")
    cflags(["-target", "x86_64-linux-gnu"])
    cxxflags(["-target", "x86_64-linux-gnu", "-std=c++17"])
    ldflags(["-target", "x86_64-linux-gnu"])
```

## Scripts Wrapper Zig

### zig-c++.bat (exemple)
```batch
@echo off
C:\Zig\zig-x86_64-windows-0.16.0\zig.exe c++ %*
```

### zig-cc.bat (exemple)
```batch
@echo off
C:\Zig\zig-x86_64-windows-0.16.0\zig.exe cc %*
```

## Avantages de Zig pour Cross-Compilation

1. **Pas de cross-toolchain complexe** : Zig remplace binutils, gcc, libc, etc.
2. **Reproductibilité** : Builds identiques sur toutes les machines
3. **Simplicité** : Un seul exécutable Zig au lieu de dizaines de composants
4. **Vitesse** : Compilation rapide avec cache intelligent
5. **Support multi-plateformes** : Windows, Linux, macOS, BSD, etc.

## Plateformes cibles supportées par Zig

Zig peut compiler pour :
- Linux (x86_64, ARM64, ARM, RISC-V, etc.)
- Windows (x86_64, ARM64)
- macOS (x86_64, ARM64)
- FreeBSD, OpenBSD, NetBSD
- WebAssembly

## Dépannage

**Erreur "zig command not found"** :
- Vérifiez que le chemin vers zig.exe est correct dans le .jenga
- Ajustez `archiver(r"C:\Zig\...")` avec votre installation

**Erreur de linking** :
- Vérifiez que les scripts wrapper (zig-c++.bat) sont accessibles
- Vérifiez les permissions d'exécution des scripts

**Binaire ne s'exécute pas sur Linux** :
- Vérifiez l'architecture : `uname -m` (doit être x86_64)
- Vérifiez la libc : Le binaire utilise glibc (GNU libc)

**Incompatibilité glibc** :
- Si vous ciblez un vieux Linux, ajustez le target triple :
  - `x86_64-linux-gnu.2.17` (CentOS 6)
  - `x86_64-linux-musl` (Alpine Linux, statique)

## Alternatives

Si vous ne pouvez pas utiliser Zig, d'autres solutions de cross-compilation existent :
- **MinGW-w64** : Windows → Linux (limité)
- **Docker** : Build dans un container Linux
- **WSL** : Compilation directe dans le sous-système Linux
- **Clang + sysroot** : Clang avec un sysroot Linux extrait

Cependant, Zig reste la solution la plus simple et portable.

## Étapes suivantes

- **14_cross_compile** : Autre exemple de cross-compilation
- **24_all_platforms** : Compilation multi-plateformes avec filtrage
- Essayez de cibler d'autres plateformes : `x86_64-macos`, `aarch64-linux-musl`
