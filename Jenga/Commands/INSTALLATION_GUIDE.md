# 📚 Guide d'Installation - Jenga Documentation System v2.0

## 🎯 Vue d'Ensemble

Le nouveau système de documentation Jenga génère automatiquement une documentation API professionnelle depuis vos commentaires Doxygen C++.

### ✨ Nouveautés v2.0

- ✅ **Parse complet des signatures C++** (templates, modifiers, paramètres)
- ✅ **Nouveaux tags Doxygen** : `@class`, `@struct`, `@enum`, `@function`, `@var`, `@macro`
- ✅ **Liens fonctionnels** entre éléments et fichiers
- ✅ **Navigation multi-niveau** : fichiers ↔ namespaces ↔ types
- ✅ **Statistiques avancées** avec couverture de documentation
- ✅ **Design moderne** avec émojis, badges et tables
- ✅ **Index alphabétique** complet
- ✅ **Graphe de dépendances** entre fichiers

## 📦 Installation

### 1. Copier les Fichiers

Copiez les 4 fichiers Python dans votre installation Jenga :

```bash
# Depuis le répertoire outputs/
cp jenga_docs_parser.py ~/Jenga/commands/
cp jenga_docs_extractor.py ~/Jenga/commands/
cp jenga_docs_markdown.py ~/Jenga/commands/
cp docs_command.py ~/Jenga/commands/docs.py
```

**Important** : Le fichier `docs_command.py` doit être renommé en `docs.py` dans le répertoire `commands/`.

### 2. Vérifier l'Installation

```bash
cd votre-workspace
jenga docs --help
```

Vous devriez voir :

```
usage: jenga docs [-h] {extract,stats,list,clean} ...

Génération de documentation pour les projets Jenga

positional arguments:
  {extract,stats,list,clean}
    extract             Extraire la documentation depuis les sources
    stats               Afficher les statistiques de documentation
    list                Lister les projets documentables
    clean               Nettoyer la documentation générée
```

## 🚀 Utilisation Rapide

### Générer la Documentation

```bash
# Tous les projets du workspace
jenga docs extract

# Un projet spécifique
jenga docs extract --project NKCore

# Avec membres privés
jenga docs extract --project NKCore --include-private

# Mode verbeux (pour déboguer)
jenga docs extract --project NKCore --verbose
```

### Explorer la Documentation

```bash
# Ouvrir dans VS Code
code docs/NKCore/markdown/index.md

# Ou dans votre navigateur Markdown préféré
# La documentation est dans: docs/[projet]/markdown/
```

### Autres Commandes

```bash
# Lister les projets documentables
jenga docs list

# Statistiques
jenga docs stats
jenga docs stats --project NKCore

# Nettoyer
jenga docs clean
jenga docs clean --project NKCore
```

## 📝 Format des Commentaires

### Style Recommandé : Doxygen

```cpp
/**
 * @class NkVector3
 * @brief Vecteur 3D pour positions et directions
 * 
 * Structure légère (12 bytes) de type POD pour représenter
 * des vecteurs 3D en espace cartésien.
 * 
 * @note Type POD - peut être copié avec memcpy
 * @threadsafe Oui (pas de state partagé)
 * 
 * @example Usage basique
 * @code
 * NkVector3 position(10.0f, 5.0f, 0.0f);
 * position += velocity * deltaTime;
 * @endcode
 * 
 * @author Rihen
 * @since Version 1.0.0
 */
class NK_API NkVector3 {
public:
    /**
     * @brief Calcule le produit scalaire de deux vecteurs
     * 
     * @param[in] a Premier vecteur
     * @param[in] b Deuxième vecteur
     * 
     * @return Produit scalaire (a·b)
     * @retval 0.0f Si les vecteurs sont perpendiculaires
     * 
     * @complexity O(1)
     * @threadsafe
     * 
     * @see Cross() pour le produit vectoriel
     */
    static float Dot(const NkVector3& a, const NkVector3& b);
    
    /**
     * @var x
     * Composante X du vecteur
     */
    float x;
    
    /// Composante Y du vecteur (style inline)
    float y;
    
    float z;  ///< Composante Z (style trailing)
};
```

### Tags Supportés

#### Tags de Type (nouveaux)
- `@class NomClasse` - Force le type class
- `@struct NomStruct` - Force le type struct  
- `@enum NomEnum` - Force le type enum
- `@union NomUnion` - Force le type union
- `@function NomFonction` - Force le type fonction
- `@var type nom` - Pour variables globales/membres
- `@macro NOM_MACRO` - Pour macros

#### Tags de Documentation
- `@brief` - Description courte (une ligne)
- `@param[in|out|in/out] nom` - Paramètre avec direction
- `@tparam T` - Paramètre template
- `@return` - Description du retour
- `@retval valeur` - Valeur spécifique de retour
- `@throw exception` - Exception lancée

#### Tags d'Exemples
- `@example titre`
- `@code ... @endcode` - Bloc de code

#### Tags de Notes
- `@note` - Note importante
- `@warning` - Avertissement
- `@attention` - Attention spéciale

#### Tags de Références
- `@see element` - Voir aussi (crée un lien)
- `@sa element` - Voir aussi (alias)

#### Tags de Métadonnées
- `@author nom` - Auteur
- `@date date` - Date
- `@since version` - Depuis quelle version
- `@deprecated raison` - Élément déprécié

#### Tags de Performance
- `@complexity O(n)` - Complexité algorithmique
- `@threadsafe` - Thread-safe
- `@notthreadsafe` - Non thread-safe

## 📁 Structure Générée

```
docs/
└── NKCore/
    └── markdown/
        ├── index.md              # Page d'accueil avec stats
        ├── search.md            # Index alphabétique A-Z
        ├── api.md               # Vue d'ensemble API
        ├── stats.md             # Statistiques détaillées
        │
        ├── files/               # Documentation par fichier
        │   ├── index.md
        │   ├── NkVector3_h.md
        │   ├── NkMatrix4_h.md
        │   └── ...
        │
        ├── namespaces/          # Documentation par namespace
        │   ├── index.md
        │   ├── nkentseu_core.md
        │   ├── nkentseu_math.md
        │   └── ...
        │
        └── types/               # Documentation par type
            ├── index.md
            ├── classes.md       # Toutes les classes
            ├── structs.md       # Toutes les structures
            ├── enums.md         # Tous les enums
            ├── functions.md     # Toutes les fonctions
            └── ...
```

## 🔗 Liens Fonctionnels

Le système crée automatiquement des liens entre :

1. **Fichiers** → Éléments qu'ils définissent
2. **Éléments** → Fichiers où ils sont définis
3. **Namespaces** → Éléments qu'ils contiennent
4. **Types** → Instances de ce type
5. **@see** → Éléments référencés
6. **Includes** → Fichiers inclus

### Exemples de Liens

```markdown
<!-- Lien vers une classe dans un autre fichier -->
[`NkVector3`](./files/NkVector3_h.md#nkentseu-math-nkvector3)

<!-- Lien vers une méthode dans le même fichier -->
[`Normalize`](#nkentseu-math-nkvector3-normalize)

<!-- Lien vers un namespace -->
[`nkentseu::core`](./namespaces/nkentseu_core.md)
```

## 🎨 Exemple de Rendu

Voici ce que vous obtiendrez :

### Page de Classe

```markdown
# 📄 NkVector3.h

## 🏛️ Classes (1)

#### 🏛️ `NkVector3`

`public`

```cpp
class NkVector3
```

**Vecteur 3D pour positions et directions**

Structure légère (12 bytes) de type POD.

**Voir Aussi:**
- [`NkVector2`](./NkVector2_h.md#nkentseu-math-nkvector2)
- [`NkMatrix4`](./NkMatrix4_h.md#nkentseu-math-nkmatrix4)

*Défini dans: `Core/NKCore/src/NKCore/Math/NkVector3.h:42`*

---

### ⚙️ Méthodes (5)

#### 🔧 `Dot`

`static` `noexcept`

```cpp
static float Dot(const NkVector3& a, const NkVector3& b) noexcept
```

**Calcule le produit scalaire**

**Paramètres:**

| Nom | Type | Description |
|-----|------|-------------|
| `a` | `const NkVector3&` | [in] Premier vecteur |
| `b` | `const NkVector3&` | [in] Deuxième vecteur |

**Retour:** Produit scalaire (a·b)

**Voir Aussi:**
- [`Cross`](#nkentseu-math-nkvector3-cross)

*Complexité: O(1) | Thread-safety: Thread-safe*

*Défini dans: `Core/NKCore/src/NKCore/Math/NkVector3.h:87`*
```

## 🐛 Dépannage

### Problème : "Aucun élément documenté"

**Causes possibles :**

1. **Commentaires non reconnus**
   ```cpp
   // ❌ Ceci ne sera PAS extrait
   // Simple commentaire
   void Function();
   
   /// ✅ Ceci SERA extrait
   /// Description de la fonction
   void Function();
   
   /** ✅ Ceci SERA extrait */
   void Function();
   ```

2. **Fichiers non trouvés**
   - Vérifiez que le projet a un dossier `src/` ou `include/`
   - Utilisez `--verbose` pour voir les répertoires scannés

3. **Extensions non supportées**
   - Extensions supportées : `.h`, `.hpp`, `.hxx`, `.hh`, `.cpp`, `.cxx`, `.cc`, `.c`, `.inl`

### Problème : "Liens cassés"

Les liens sont générés automatiquement. Si un lien est cassé :

1. Vérifiez que l'élément cible existe bien
2. Vérifiez l'orthographe dans `@see`
3. Utilisez le nom complet avec namespace si nécessaire

### Problème : "Signature mal parsée"

Si une signature n'est pas correctement reconnue :

1. Utilisez les tags de type : `@class`, `@function`, etc.
2. Assurez-vous que la signature est sur les 10 premières lignes après le commentaire
3. Signalez le cas sur GitHub pour amélioration

## 📊 Statistiques

La page `stats.md` affiche :

- Nombre de fichiers analysés
- Éléments par type (classes, fonctions, etc.)
- Couverture de documentation (% d'éléments bien documentés)
- Paramètres moyens par fonction
- Top 10 des fichiers les plus documentés

**Bien documenté = élément avec `@brief` ET description**

## 🎯 Bonnes Pratiques

### 1. Commencez par l'API Publique

Documentez d'abord les classes et fonctions publiques :

```cpp
/**
 * @class NkRenderer
 * @brief Système de rendu principal
 * 
 * Gère le pipeline de rendu complet incluant...
 */
class NK_API NkRenderer {
public:
    /** @brief Initialise le renderer */
    void Initialize();
    
private:
    // Pas besoin de documenter si --include-private n'est pas utilisé
    void InternalUpdate();
};
```

### 2. Documentez les Directions de Paramètres

```cpp
/**
 * @param[in] input   Données en entrée (non modifiées)
 * @param[out] output Résultat calculé
 * @param[in,out] buffer Tampon modifié
 */
void Process(const Data& input, Result& output, Buffer& buffer);
```

### 3. Ajoutez des Exemples

```cpp
/**
 * @example Création d'un vecteur
 * @code
 * NkVector3 v(1.0f, 2.0f, 3.0f);
 * v.Normalize();
 * @endcode
 */
```

### 4. Documentez la Complexité

```cpp
/**
 * @brief Recherche linéaire
 * @complexity O(n)
 */
int Find(const std::vector<int>& data, int value);
```

### 5. Indiquez la Thread-Safety

```cpp
/**
 * @threadsafe
 */
class ThreadSafeQueue { };

/**
 * @notthreadsafe
 * @warning Utilisez des mutex si accès concurrent
 */
class Cache { };
```

## 🔄 Intégration CI/CD

### GitHub Actions

```yaml
name: Documentation

on: [push]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Generate Documentation
        run: |
          python -m pip install jenga-build-system
          jenga docs extract
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Régénérer la doc si des fichiers .h/.cpp modifiés
if git diff --cached --name-only | grep -E '\.(h|hpp|cpp)$'; then
    echo "📚 Updating documentation..."
    jenga docs extract --project YourProject
    git add docs/
fi
```

## 📚 Ressources

- **Doxygen Manual** : https://www.doxygen.nl/manual/
- **Markdown Guide** : https://www.markdownguide.org/
- **Jenga GitHub** : https://github.com/RihenUniverse/Jenga

## 💡 Astuces

### VS Code

Installez l'extension "Markdown All in One" pour :
- Prévisualisation live (`Ctrl+Shift+V`)
- Navigation dans les liens (`Ctrl+Click`)
- Table des matières automatique

### Recherche Rapide

```bash
# Chercher un élément dans la documentation
grep -r "NomFonction" docs/*/markdown/

# Chercher dans un type spécifique
grep -r "pattern" docs/*/markdown/types/classes.md
```

### Export HTML

```bash
# Avec pandoc (à venir)
pandoc docs/NKCore/markdown/index.md -o index.html --standalone
```

## 🆘 Support

**Problèmes ?** Créez une issue sur GitHub avec :
1. La commande utilisée
2. Le code source qui pose problème
3. La sortie de `--verbose`

**Suggestions ?** Les pull requests sont bienvenues !

---

*Documentation générée avec ❤️ par Jenga Build System v2.0*
