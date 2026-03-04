# Cours 01 — Mathématiques pour le Graphique Informatique
**Prérequis :** C++ intermédiaire  
**Durée estimée :** 10 semaines  
**Objectif :** Maîtriser toutes les mathématiques nécessaires à la programmation graphique, implémentées from scratch en C++.

---

## Unité 1 — Vecteurs et espaces vectoriels (2 semaines)

### Semaine 1
- Vecteurs 2D, 3D, 4D : définition, représentation mémoire
- Implémentation C++ : `Vec2f`, `Vec3f`, `Vec4f` avec templates
- Opérations : addition, soustraction, multiplication scalaire
- Produit scalaire (dot product) : formule, interprétation géométrique
- Norme et normalisation
- **TP :** Implémenter une bibliothèque `nkmath` complète avec tests unitaires

### Semaine 2
- Produit vectoriel (cross product) : formule 3D, règle de la main droite
- Projection orthogonale d'un vecteur sur un autre
- Décomposition d'un vecteur (composante parallèle / perpendiculaire)
- Interpolation linéaire (lerp), quadratique, cubique
- Coordonnées barycentriques
- **TP :** Ray-point et ray-segment intersection 2D from scratch

---

## Unité 2 — Matrices (2 semaines)

### Semaine 3
- Matrices 2x2, 3x3, 4x4 : stockage row-major vs column-major
- Implémentation C++ : `Mat2f`, `Mat3f`, `Mat4f`
- Multiplication matricielle : algorithme naïf O(n³)
- Matrices identité, diagonale, symétrique
- Transposée
- **TP :** Implémenter toutes les opérations matricielles, vérifier avec des cas connus

### Semaine 4
- Déterminant (2x2, 3x3, 4x4 par cofacteurs)
- Inverse d'une matrice : méthode de Gauss-Jordan
- Changement de base : comprendre la signification géométrique
- Matrices de transformation 2D : translation (homogène), rotation, échelle, cisaillement
- Composition de transformations
- **TP :** Moteur de transformation 2D, hiérarchie de scène parent/enfant

---

## Unité 3 — Transformations 3D (2 semaines)

### Semaine 5
- Matrices de rotation 3D : Rx, Ry, Rz
- Problème du gimbal lock
- Angles d'Euler : ordre de composition (XYZ, ZYX…)
- Matrices de scale et translation homogènes (4x4)
- Espace objet → espace monde → espace caméra → espace clip
- **TP :** Implémenter la chaîne de transformation MVP (Model-View-Projection) from scratch

### Semaine 6
- Quaternions : définition, forme `q = w + xi + yj + zk`
- Multiplication de quaternions, conjugué, norme, inverse
- Rotation par quaternion : `q * v * q⁻¹`
- Conversion quaternion ↔ matrice ↔ angles d'Euler
- SLERP (Spherical Linear Interpolation)
- **TP :** Système d'animation de caméra à la première personne avec quaternions

---

## Unité 4 — Géométrie computationnelle (2 semaines)

### Semaine 7
- Droites et plans : équations paramétriques et implicites
- Tests d'intersection : rayon/plan, rayon/triangle (Möller–Trumbore)
- Tests d'intersection : rayon/sphère, rayon/AABB
- Coordonnées barycentriques pour les triangles 3D
- Winding order et normales de surface
- **TP :** Raytracer minimaliste CPU : sphère + plan + lumière ponctuelle

### Semaine 8
- AABB (Axis-Aligned Bounding Boxes) : construction, test d'intersection
- OBB (Oriented Bounding Boxes) : SAT (Separating Axis Theorem)
- Convex hull 2D : algorithme Graham Scan
- Frustum culling : extraction des 6 plans du frustum
- Test point-dans-convexe, test AABB-frustum
- **TP :** Frustum culling d'une scène de 10 000 objets, mesure de performance

---

## Unité 5 — Courbes et surfaces (1 semaine)

### Semaine 9
- Courbes de Bézier : degré 1, 2, 3 — algorithme de De Casteljau
- B-Splines : knot vector, base functions
- Courbes de Hermite et Catmull-Rom
- Subdivision de courbes
- Surfaces de Bézier (patch bilinéaire, bicubique)
- **TP :** Éditeur de courbe de Bézier 2D interactif, export de points interpolés

---

## Unité 6 — Algèbre pour le rendu (1 semaine)

### Semaine 10
- Espaces de couleur : RGB, HSV, HSL, YUV, Lab — conversions
- Gamma correction et espace linéaire
- Matrices de projection : perspective (FOV, near, far) et orthographique
- Projection NDC → pixels (viewport transform)
- Bruit procédural : bruit de Perlin, bruit de valeur, fractals (fBm)
- **TP :** Génération de terrain procédural avec Perlin noise, rendu software

---

## Projet Final

Implémenter une bibliothèque mathématique complète `nkmath` comprenant :
- Vecteurs 2/3/4D avec toutes les opérations
- Matrices 2x2, 3x3, 4x4
- Quaternions avec SLERP
- Courbes de Bézier
- Intersection rayon/primitives
- Frustum culling
- Documentation Doxygen, tests unitaires complets

**Critères d'évaluation :** Exactitude numérique, performance (benchmark vs GLM), qualité du code C++, tests.
