# Tests Unitest / Unitest Tests

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

**Unitest** est le framework de tests C++ intégré à Jenga. Les sources et un
binaire précompilé sont livrés avec le package — aucune dépendance externe
(pas de GoogleTest, Catch2…).

### 1. Activer Unitest

Au niveau workspace, déclarez le mode :

```python
with workspace("UnitWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.LINUX])
    targetarchs([TargetArch.X86_64])

    with unitest() as u:
        u.Precompiled()       # utilise la lib précompilée livrée (défaut)
        # ou
        # u.Compile(kind="STATIC_LIB", objDir="...", targetDir="...")
```

- **`Precompiled()`** : utilise le binaire Unitest fourni — démarrage immédiat.
- **`Compile(...)`** : recompile Unitest depuis les sources (utile en
  cross-compilation ou pour une plateforme exotique).

### 2. Déclarer une suite de tests

Le bloc `with test():` **doit être imbriqué directement** dans un `with
project():`. Il crée automatiquement un projet `<Projet>_Tests` dépendant du
projet parent et de Unitest.

```python
with project("Calculator"):
    staticlib()
    language("C++"); cppdialect("C++17")
    files(["src/**.cpp"])
    includedirs(["include"])

    with test():
        testfiles(["tests/**.cpp"])
        testmainfile("src/main.cpp")    # exclut le main du projet testé
        testoptions(["--verbose"])
```

### 3. Écrire un test

```cpp
#include <Unitest/Unitest.h>

TEST_CASE(MathSuite, Addition) {
    ASSERT_EQUAL(4, 2 + 2);
    ASSERT_TRUE(3 > 2);
}

TEST(SimpleCheck) {
    ASSERT_NEAR(3.14, 3.14159, 0.01);
}
```

Macros disponibles : `TEST_CASE(suite, nom)`, `TEST(nom)`, `ASSERT_EQUAL`,
`ASSERT_TRUE`, `ASSERT_NULL`, `ASSERT_LESS`, `ASSERT_NEAR`, `ASSERT_THROWS`,
`ASSERT_CONTAINS`. Le framework fournit aussi du **benchmarking** et du
**profilage** (flamegraph).

### 4. Compiler et exécuter

```bash
jenga test                              # compile + lance toutes les suites
jenga test --project Calculator_Tests   # une suite précise
jenga test --config Debug --no-build    # sans recompiler
```

`jenga test` continue même si une suite échoue, et agrège les résultats dans un
rapport console.

### 5. Politiques de workspace

```python
disableunittestcompilation(True)   # ou dutc(True) — ne pas compiler les tests
disableunittestexecution(True)     # ou dute(True) — ne pas exécuter les tests
```

### 6. Erreurs fréquentes

- `test context must be placed directly inside a project block` → le bloc
  `with test():` doit être imbriqué dans `with project(...):`.
- Unitest non configuré → ajouter `with unitest() as u: u.Precompiled()` dans le
  workspace avant les projets qui utilisent `test()`.

---

## English

**Unitest** is the C++ testing framework built into Jenga. Sources and a
precompiled binary ship with the package — no external dependency
(no GoogleTest, Catch2…).

### 1. Enable Unitest

Declare the mode at workspace level:

```python
with workspace("UnitWorkspace"):
    configurations(["Debug", "Release"])
    targetoses([TargetOS.LINUX])
    targetarchs([TargetArch.X86_64])

    with unitest() as u:
        u.Precompiled()       # use the shipped precompiled lib (default)
        # or
        # u.Compile(kind="STATIC_LIB", objDir="...", targetDir="...")
```

- **`Precompiled()`**: uses the bundled Unitest binary — instant start.
- **`Compile(...)`**: rebuilds Unitest from source (useful for
  cross-compilation or exotic platforms).

### 2. Declare a test suite

The `with test():` block **must be nested directly** inside a `with
project():`. It automatically creates a `<Project>_Tests` project depending on
the parent project and on Unitest.

```python
with project("Calculator"):
    staticlib()
    language("C++"); cppdialect("C++17")
    files(["src/**.cpp"])
    includedirs(["include"])

    with test():
        testfiles(["tests/**.cpp"])
        testmainfile("src/main.cpp")    # exclude the tested project's main
        testoptions(["--verbose"])
```

### 3. Write a test

```cpp
#include <Unitest/Unitest.h>

TEST_CASE(MathSuite, Addition) {
    ASSERT_EQUAL(4, 2 + 2);
    ASSERT_TRUE(3 > 2);
}

TEST(SimpleCheck) {
    ASSERT_NEAR(3.14, 3.14159, 0.01);
}
```

Available macros: `TEST_CASE(suite, name)`, `TEST(name)`, `ASSERT_EQUAL`,
`ASSERT_TRUE`, `ASSERT_NULL`, `ASSERT_LESS`, `ASSERT_NEAR`, `ASSERT_THROWS`,
`ASSERT_CONTAINS`. The framework also provides **benchmarking** and
**profiling** (flamegraph).

### 4. Build and run

```bash
jenga test                              # build + run all suites
jenga test --project Calculator_Tests   # a specific suite
jenga test --config Debug --no-build    # without rebuilding
```

`jenga test` keeps going even if a suite fails, and aggregates results into a
console report.

### 5. Workspace policies

```python
disableunittestcompilation(True)   # or dutc(True) — don't compile tests
disableunittestexecution(True)     # or dute(True) — don't run tests
```

### 6. Common errors

- `test context must be placed directly inside a project block` → the
  `with test():` block must be nested inside `with project(...):`.
- Unitest not configured → add `with unitest() as u: u.Precompiled()` to the
  workspace before any project that uses `test()`.

See example `04_unit_tests`.
