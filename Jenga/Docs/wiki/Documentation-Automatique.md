# Documentation Automatique

La commande `jenga docs` permet d'extraire une documentation API à partir du code C/C++.

## Commandes principales

```bash
jenga docs extract
jenga docs extract --project MonProjet --include-private --verbose
jenga docs list
jenga docs stats
jenga docs clean
```

## Tags de commentaires reconnus

- `@brief`
- `@param`
- `@tparam`
- `@return`, `@retval`
- `@throws`
- `@example`, `@code ... @endcode`
- `@note`, `@warning`, `@see`
- `@since`, `@deprecated`, `@author`, `@date`, `@complexity`

## Exemples de commentaires

```cpp
/**
 * @brief Additionne deux nombres.
 * @param a Valeur 1
 * @param b Valeur 2
 * @return Somme des valeurs
 * @note Complexité O(1)
 */
int Add(int a, int b);
```

```cpp
/// @brief Retourne la version du moteur
/// @return Chaîne de version
const char* GetEngineVersion();
```

## Structure de sortie

```text
docs/
  MonProjet/
    markdown/
      index.md
      api.md
      search.md
      stats.md
      files/
      namespaces/
      types/
```

## Note importante

Le paramètre `--format html|pdf|all` existe côté CLI, mais la génération réellement implémentée dans le code actuel est la sortie Markdown.
