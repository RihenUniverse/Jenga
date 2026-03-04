# Cours 13 — Realtime Rendering Avancé
**Prérequis :** Cours 05 ou 06, 04, 09  
**Durée estimée :** 12 semaines  
**Objectif :** Maîtriser les techniques de rendu temps réel état de l'art utilisées dans les productions AAA.

---

## Unité 1 — Physically Based Rendering approfondi (2 semaines)

### Semaine 1
- Radiométrie : radiance, irradiance, BRDF définition formelle
- Équation du rendu (rendering equation) de Kajiya
- Microfacet BRDF : Cook-Torrance complet
  - Distribution des normales (NDF) : GGX/Trowbridge-Reitz, Beckmann, Phong
  - Géométrie (masquage/shadowing) : Smith GGX, Schlick-GGX
  - Fresnel : Schlick, Lazarov, dielectrique vs conducteur
- Energy conservation : split-sum approximation (Brian Karis)
- **TP :** Material test sphere avec toutes les combinaisons metallic/roughness

### Semaine 2
- IBL (Image Based Lighting) from scratch :
  - Diffuse irradiance : spherical harmonics (SH, ordre 2 et 3)
  - Specular : pre-filtered environment map (GGX convolution), BRDF LUT
  - Génération offline avec compute shader
- Clearcoat, sheen, transmission, subsurface scattering (SSS) simplifié
- Multi-scattering compensation (Kulla-Conty)
- Glints et sparkles (microsurfaces)
- **TP :** Matériaux avancés : voiture (clearcoat + anisotropie), tissu (sheen), peau (SSS)

---

## Unité 2 — Illumination globale approximée (2 semaines)

### Semaine 3
- Light probes : capture, placement, blending spatial
- Radiance caching : Light Probe Grid, importance sampling
- Voxel Cone Tracing (VXGI) simplifié
- Lumen (Unreal) concept : surface cache, radiance cache
- Screen Space GI (SSGI) : ray marching sur le depth buffer
- **TP :** Système de light probes avec blending interpolé dans une scène intérieure

### Semaine 4
- Réflexions : SSR (Screen Space Reflections) amélioré
- Reflection captures (cube map + parallax correction)
- Planar reflections
- Raytraced reflections hybrides (quand disponible)
- Area lights : LTC (Linearly Transformed Cosines) approximation
- **TP :** Comparaison SSR vs LTC vs raytraced reflections, trade-off qualité/performance

---

## Unité 3 — Ombres avancées (2 semaines)

### Semaine 5
- VSM (Variance Shadow Maps) : filtrage gaussien, bleeding
- ESM (Exponential Shadow Maps)
- PCSS (Percentage Closer Soft Shadows) : recherche du bloqueur, kernel variable
- SDSM (Sample Distribution Shadow Maps) : distribution optimale des cascades
- Ray-traced soft shadows hybrides

### Semaine 6
- Ambient Occlusion :
  - SSAO : hemisphere sampling, blur bilatéral
  - HBAO+ (Horizon Based AO)
  - GTAO (Ground Truth AO) : cosine-weighted integral
  - RTAO (Ray Traced AO)
- Contact shadows : ray marching espace écran
- **TP :** Comparaison de toutes les techniques AO sur la même scène, rapport qualité/perf

---

## Unité 4 — Anti-aliasing et upscaling (1 semaine)

### Semaine 7
- MSAA : fonctionnement interne, coût en bandwidth
- FXAA : implémentation complète du shader
- TAA (Temporal Anti-Aliasing) : jitter de caméra, accumulation temporelle, ghosting, rejection
- DLSS (concept) vs FSR (AMD, open source) vs TAAU
- FSR 1.0 implementation : EASU (upscaling) + RCAS (sharpening)
- Velocity buffer : reconstruction du mouvement pour TAA
- **TP :** Implémenter TAA complet avec velocity buffer, comparer avec FXAA et MSAA

---

## Unité 5 — Post-processing pipeline (2 semaines)

### Semaine 8
- Bloom : dual Kawase blur, threshold, scatter, dirt mask
- Depth of Field : CoC (Circle of Confusion), gather-based DoF, bokeh shapes
- Motion blur : per-object et camera, reconstruction filter
- Lens flares et vignette
- Chromatic aberration, film grain

### Semaine 9
- Tone mapping : Reinhard, ACES filmic (full matrix), Lottes, Uchimura
- Color grading : LUT 3D (Look-Up Table), courbes de contraste
- Eye adaptation (auto-exposure) : histogram GPU, smooth adaptation
- Color space pipeline : linear → tonemap → gamma → output
- HDR display output : HDR10, PQ curve, metadata
- **TP :** Pipeline post-process complet : bloom → DoF → motion blur → ACES → color grade → HDR

---

## Unité 6 — Techniques spécialisées (1 semaine)

### Semaine 10
- Rendu de végétation : LOD système, billboards alpha tested, wind animation
- Eau et océan : FFT ocean (Tessendorf), foam, depth fog, Fresnel
- Particules volumétriques : raymarching dans un volume, absorption, scattering
- Atmospheric scattering : Rayleigh + Mie, Bruneton sky model simplifié
- Subsurface scattering pour la peau : screen-space SSS, pre-integrated skin
- **TP :** Scène extérieure : ciel Bruneton, océan FFT, végétation LOD

---

## Unité 7 — Rendu différé avancé et clustering (2 semaines)

### Semaine 11
- Clustered shading : subdivision du frustum en clusters 3D, assignation de lumières
- Tiled forward rendering (Forward+) : liste de lumières par tile
- Deferred vs Forward+ : comparaison sur des scènes à 1000+ lumières
- Virtual Shadow Maps : pages virtuelles, feedback pass
- Nanite (concept) : simplification de mesh hiérarchique, représentation sur disque

### Semaine 12
- Lumen-like GI : radiance cache sur surfaces, propagation
- Temporal history et ghosting : robustesse aux mouvements rapides
- Path tracing de référence : comparaison avec le rendu temps réel
- **TP :** Renderer complet Sponza avec 500 lumières dynamiques en clustered forward+, 60fps 1080p

---

## Projet Final

**Renderer AAA-quality** :
- Clustered forward+ avec 1000 lumières
- PBR + IBL + SH diffuse
- PCSS + SDSM
- TAA + FSR 1.0
- Post-process complet (bloom, DoF, ACES, LUT)
- Atmospheric scattering
- GTAO

**Rapport technique :** Comparaison visuelle avec UE5/Unity, justification des choix techniques.
