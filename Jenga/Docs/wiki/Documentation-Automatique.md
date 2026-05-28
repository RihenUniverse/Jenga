# Documentation Automatique / Automatic Documentation

**Langues / Languages :** [Français](#français) · [English](#english)

---

## Français

La commande `jenga docs` extrait une documentation API à partir du code C/C++
(signatures + commentaires de style Doxygen).

### Commandes principales

```bash
jenga docs extract
jenga docs extract --project MonProjet --include-private --verbose
jenga docs list
jenga docs stats
jenga docs clean
```

### Éléments extraits

Classes, structures, énumérations, unions, fonctions, méthodes, variables,
macros — avec leurs paramètres, types de retour, exceptions et modificateurs
(`const`, `static`, `virtual`, `override`, `inline`, `constexpr`, `noexcept`).

### Tags de commentaires reconnus

`@brief` · `@param` · `@tparam` · `@return` / `@retval` · `@throws` ·
`@example` / `@code … @endcode` · `@note` · `@warning` · `@see` · `@since` ·
`@deprecated` · `@author` · `@date` · `@complexity`.

### Exemples de commentaires

```cpp
/**
 * @brief Additionne deux nombres.
 * @param a Première valeur
 * @param b Seconde valeur
 * @return Somme des valeurs
 * @note Complexité O(1)
 */
int Add(int a, int b);

/// @brief Retourne la version du moteur
/// @return Chaîne de version
const char* GetEngineVersion();
```

### Structure de sortie

```text
docs/
└── MonProjet/
    └── markdown/
        ├── index.md
        ├── api.md
        ├── search.md
        ├── stats.md
        ├── files/
        ├── namespaces/
        └── types/
```

### Outils optionnels

- `pandoc` — conversion Markdown → PDF.
- Modules Python `markdown`, `pygments` — coloration syntaxique (extra
  `pip install jenga[docs]`).

### Note

Les options `--format html|pdf|all` existent côté CLI, mais la génération
réellement aboutie dans le code actuel est la **sortie Markdown**.

---

## English

The `jenga docs` command extracts API documentation from C/C++ code
(signatures + Doxygen-style comments).

### Main commands

```bash
jenga docs extract
jenga docs extract --project MyProject --include-private --verbose
jenga docs list
jenga docs stats
jenga docs clean
```

### Extracted elements

Classes, structs, enums, unions, functions, methods, variables, macros — with
their parameters, return types, exceptions and modifiers (`const`, `static`,
`virtual`, `override`, `inline`, `constexpr`, `noexcept`).

### Recognized comment tags

`@brief` · `@param` · `@tparam` · `@return` / `@retval` · `@throws` ·
`@example` / `@code … @endcode` · `@note` · `@warning` · `@see` · `@since` ·
`@deprecated` · `@author` · `@date` · `@complexity`.

### Comment examples

```cpp
/**
 * @brief Adds two numbers.
 * @param a First value
 * @param b Second value
 * @return Sum of the values
 * @note O(1) complexity
 */
int Add(int a, int b);

/// @brief Returns the engine version
/// @return Version string
const char* GetEngineVersion();
```

### Output structure

```text
docs/
└── MyProject/
    └── markdown/
        ├── index.md
        ├── api.md
        ├── search.md
        ├── stats.md
        ├── files/
        ├── namespaces/
        └── types/
```

### Optional tools

- `pandoc` — Markdown → PDF conversion.
- Python modules `markdown`, `pygments` — syntax highlighting (extra
  `pip install jenga[docs]`).

### Note

The `--format html|pdf|all` options exist in the CLI, but the fully implemented
output in the current code is **Markdown**.
