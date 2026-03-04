# Cours 02 — Programmation 2D from scratch
**Prérequis :** Cours 01 (Mathématiques)  
**Durée estimée :** 8 semaines  
**Objectif :** Implémenter tous les algorithmes fondamentaux de rendu 2D sans bibliothèque graphique externe, directement sur un framebuffer.

---

## Unité 1 — Framebuffer et primitives de base (2 semaines)

### Semaine 1
- Qu'est-ce qu'un framebuffer : tableau linéaire de pixels RGBA8
- Coordonnées écran : origine en haut-gauche vs bas-gauche, conventions
- Implémentation C++ : `Framebuffer` class, `SetPixel`, `Clear`
- Format de pixel : RGBA8, ARGB, pack/unpack de couleurs
- Écriture vers une fenêtre (via NkWindow ou Win32 GDI StretchDIBits)
- **TP :** Afficher un dégradé de couleurs sur tout l'écran, 60 fps

### Semaine 2
- Algorithme de tracé de ligne : Bresenham (entier, sans flottant)
- Épaisseur de ligne, antialiasing de Xiaolin Wu
- Tracé de cercle : algorithme du point médian
- Tracé d'ellipse
- Courbe de Bézier quadratique par subdivision récursive
- **TP :** Éditeur vectoriel basique : ligne, cercle, courbe avec souris

---

## Unité 2 — Remplissage de formes (2 semaines)

### Semaine 3
- Triangle rasterization : scanline fill, edge walking
- Calcul des bounding box, clipping sur le framebuffer
- Remplissage de polygone convexe par scanline
- Règle du remplissage : even-odd vs non-zero winding
- **TP :** Rasteriser 10 000 triangles colorés, mesurer le throughput (triangles/seconde)

### Semaine 4
- Flood fill : algorithme récursif et itératif (stack)
- Remplissage avec motif (pattern fill)
- Gradient linéaire et radial sur triangle (interpolation par coordonnées barycentriques)
- Antialiasing par supersampling (SSAA 2x, 4x)
- **TP :** Rendu d'un polygone complexe non-convexe avec gradient et antialiasing

---

## Unité 3 — Transformations 2D et caméra (1 semaine)

### Semaine 5
- Application des matrices de transformation 2D (du cours 01) au rendu
- Système de coordonnées monde → caméra → écran
- Zoom, pan, rotation de la vue
- Gestion des coordonnées en virgule fixe pour la précision
- Clipping de polygones : algorithme de Sutherland–Hodgman
- **TP :** Scène 2D avec caméra mobile, zoom fluide, 50+ objets

---

## Unité 4 — Textures et images (2 semaines)

### Semaine 6
- Chargement d'images : décodeur BMP from scratch, puis lecteur TGA
- Texture mapping sur triangle : coordonnées UV, interpolation perspective-correct
- Nearest-neighbor vs bilinéaire vs bicubique
- Wrapping modes : clamp, repeat, mirror
- **TP :** Plaquer une texture sur un quad 2D, tester les différents modes

### Semaine 7
- Mipmapping : génération automatique des niveaux, sélection du niveau
- Alpha blending : modes over, multiply, additive, screen
- Compositing d'images : Porter-Duff operators
- Sprite sheet et animation frame-by-frame
- Batching de sprites pour la performance
- **TP :** Système de sprites animés avec alpha blending, 500+ sprites à 60fps

---

## Unité 5 — Rendu de texte (1 semaine)

### Semaine 8
- Format de police bitmap : atlas de glyphes, kerning table
- Rendu de texte sur framebuffer : placement de glyphes
- Chargement d'une police TrueType : lecture basique du format TTF (headers, cmap, glyf)
- Rasterisation de glyphe vectoriel : décomposition en contours de Bézier
- SDF (Signed Distance Field) pour texte scalable
- **TP :** Afficheur de texte from scratch avec une police TTF simple, rendu SDF

---

## Projet Final

**Mini-moteur 2D complet** :
- Framebuffer avec double buffering
- Rendu de sprites, texte, primitives
- Caméra 2D avec zoom/pan
- Scène de démonstration : 200+ sprites animés, texte UI, 60fps
- Profiling : identifier et éliminer les bottlenecks

**Critères :** Performance (fps stable), qualité visuelle, architecture propre du code.
