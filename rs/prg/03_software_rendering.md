# Cours 03 — Software Rendering & Pipeline Graphique
**Prérequis :** Cours 01, 02  
**Durée estimée :** 10 semaines  
**Objectif :** Implémenter un pipeline graphique 3D complet en CPU, de l'objet 3D au pixel final, en reproduisant exactement le fonctionnement d'un GPU.

---

## Unité 1 — Architecture du pipeline (1 semaine)

### Semaine 1
- Architecture du pipeline graphique moderne : vertex → primitive assembly → rasterization → fragment → output
- Comparaison CPU software renderer vs GPU hardware
- Structure d'un vertex : position, normale, UV, couleur, tangente
- Vertex buffer et index buffer : organisation mémoire
- Z-buffer (depth buffer) : principe, format, précision
- **TP :** Squelette du renderer : `SoftwareRenderer` class, pipeline stubs

---

## Unité 2 — Vertex processing (2 semaines)

### Semaine 2
- Implémentation du vertex shader en C++ : fonction `ProcessVertex(Vertex in) -> ClipVertex out`
- Transformation MVP complète from scratch
- Espace clip, NDC (Normalized Device Coordinates)
- Perspective division (homogeneous divide)
- Viewport transform : NDC → pixels
- **TP :** Afficher un cube 3D tournant avec transformation MVP correcte

### Semaine 3
- Clipping dans l'espace clip (Cohen-Sutherland 3D, Sutherland-Hodgman pour polygones)
- Gestion des triangles partiellement hors-frustum
- Back-face culling : dot product normal/vue
- Winding order cohérent (CW vs CCW)
- Near plane clipping (éviter la division par zéro)
- **TP :** Scène avec objets hors-frustum, clipping correct visible

---

## Unité 3 — Rasterisation 3D (2 semaines)

### Semaine 4
- Triangle setup : bounding box, edge functions
- Rasterisation par edge function (algorithme de Pineda)
- Interpolation perspective-correct des attributs (UV, couleur, normale)
- Calcul des coordonnées barycentriques en espace écran
- Z-buffer test et écriture
- **TP :** Rasteriser un mesh OBJ simple avec depth test

### Semaine 5
- Optimisations du rasteriseur : tiled rendering, SIMD (SSE/AVX) pour 4/8 pixels en parallèle
- Hiérarchical Z-buffer concept
- Early Z rejection
- Interpolation des attributs en espace monde vs espace écran
- **TP :** Comparer le renderer sans/avec SIMD, mesurer le speedup

---

## Unité 4 — Shading et matériaux (2 semaines)

### Semaine 6
- Modèle d'illumination de Lambert (diffuse)
- Modèle de Phong : ambient + diffuse + specular
- Blinn-Phong : half-vector, avantages
- Normales interpolées (Gouraud shading vs Phong shading)
- Normal mapping : espace tangent, TBN matrix, décodage d'une normal map
- **TP :** Scène éclairée avec Blinn-Phong et normal map, comparaison Gouraud/Phong

### Semaine 7
- Textures dans le pipeline software : lookup avec interpolation bilinéaire
- Mipmapping dans le rasteriseur : calcul de LOD par dérivées
- Ombres : shadow mapping CPU — génération de la depth map depuis la lumière
- PCF (Percentage Closer Filtering) pour ombres douces
- Multiple lights : point light, directional, spot
- **TP :** Scène avec shadow mapping, 2-3 lumières, ombres correctes

---

## Unité 5 — Chargement de modèles et scènes (1 semaine)

### Semaine 8
- Parser de fichier OBJ from scratch : vertices, normales, UVs, matériaux MTL
- Génération de normales par face et par vertex (averaging)
- Génération de tangentes pour le normal mapping (Mikktspace)
- Structures de données de scène : SceneGraph, nœuds, transformations hiérarchiques
- **TP :** Charger et afficher un modèle OBJ complexe (Sponza, Stanford Bunny)

---

## Unité 6 — Effets avancés et post-processing (2 semaines)

### Semaine 9
- Framebuffer objects (côté software) : color buffer, depth buffer, stencil buffer
- Post-processing sur le color buffer : grayscale, inversion, sepia
- Filtre de convolution : blur (Gaussian), sharpen, edge detect (Sobel)
- Tone mapping : Reinhard, filmic (ACES approximation)
- Gamma correction et espace linéaire vs sRGB
- **TP :** Pipeline de post-processing complet avec chaîne d'effets

### Semaine 10
- Transparence et order-dependent transparency : painter's algorithm, Z-sort
- OIT (Order-Independent Transparency) : depth peeling algorithm
- Fog : linear, exponential, par hauteur
- Skybox : cube map lookup software
- Ambient occlusion approximée (SSAO concept sur CPU)
- **TP :** Scène complète avec transparence OIT, fog, skybox, tone mapping

---

## Projet Final

**Software renderer complet** capable d'afficher la scène Sponza avec :
- Chargement OBJ/MTL
- Éclairage Blinn-Phong, normal mapping
- Shadow mapping avec PCF
- Post-processing (ACES tone mapping, gamma)
- Performance cible : ≥ 30fps en 800×600 sur CPU moderne (single-threaded), puis optimiser avec threading

**Rapport :** Analyse de performance par étape du pipeline, profiling flamegraph.
