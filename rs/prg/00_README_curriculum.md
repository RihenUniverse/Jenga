# Curriculum : Programmation Graphique & Systèmes Immersifs
**Langage :** C++ exclusivement  
**Niveau d'entrée :** C++ intermédiaire  
**Durée totale :** ~160 semaines (3 ans à temps plein, ou 4-5 ans en formation parallèle)

---

## Vue d'ensemble des 18 cours

| # | Cours | Semaines | Prérequis |
|---|-------|----------|-----------|
| 01 | Mathématiques pour le Graphique | 10 | Aucun |
| 02 | Programmation 2D from scratch | 8 | 01 |
| 03 | Software Rendering & Pipeline | 10 | 01, 02 |
| 04 | Shaders & Langages GPU | 6 | 01, 03 |
| 05 | OpenGL Programming | 10 | 01, 03, 04 |
| 06 | Vulkan Programming | 14 | 01, 03, 04, 05 |
| 07 | DirectX 11/12 Programming | 12 | 01, 03, 04 |
| 08 | GPGPU / GPU Computing | 10 | 01, 04 |
| 09 | Optimisation & Performance | 8 | 01–05 |
| 10 | Audio Programming from scratch | 6 | 01 |
| 11 | Moteurs de Jeu from scratch | 14 | 01–05, 09, 10 |
| 12 | Realtime Systems Programming | 8 | 09, 11 |
| 13 | Realtime Rendering Avancé | 12 | 05 ou 06, 04, 09 |
| 14 | Intelligence Artificielle from scratch | 16 | 01 |
| 15 | AR Programming from scratch | 10 | 01, 03, 05, 14 |
| 16 | VR Programming from scratch | 10 | 01, 05 ou 06, 12, 13 |
| 17 | XR Programming from scratch | 8 | 15, 16, 13 |
| 18 | System & Immersive Engineering (Capstone) | 12 | Tous |

---

## Chemins de progression recommandés

### Chemin A — Graphique temps réel (jeu / simulation)
```
01 → 02 → 03 → 04 → 05 → 09 → 11 → 12 → 13 → 18
```
Puis spécialisation : + 06 (Vulkan) ou + 07 (DirectX) ou + 08 (GPGPU)

### Chemin B — XR / Immersif
```
01 → 02 → 03 → 04 → 05 → 09 → 11 → 12 → 13 → 14 → 15 → 16 → 17 → 18
```

### Chemin C — IA graphique
```
01 → 03 → 04 → 05 → 08 → 14 → 13 → 18
```

### Chemin D — Systèmes bas niveau
```
01 → 03 → 04 → 06 → 08 → 09 → 12 → 13 → 18
```

---

## Jalons d'apprentissage

**Après le cours 03** — L'étudiant peut écrire un renderer 3D complet CPU.  
**Après le cours 05** — L'étudiant peut développer une application 3D OpenGL complète.  
**Après le cours 06** — L'étudiant comprend le rendu GPU moderne au niveau du driver.  
**Après le cours 11** — L'étudiant peut construire un moteur de jeu complet.  
**Après le cours 13** — L'étudiant peut implémenter des techniques de rendu AAA.  
**Après le cours 14** — L'étudiant peut entraîner et déployer des modèles de ML.  
**Après le cours 18** — L'étudiant est prêt pour un poste de programmeur graphique sénior.

---

## Philosophie pédagogique

> **"From scratch" ne signifie pas réinventer inutilement. Cela signifie comprendre chaque couche avant de l'utiliser."**

- Chaque concept est **implémenté avant d'être utilisé via une API**
- Les bibliothèques tierces ne sont autorisées qu'après avoir implémenté l'équivalent
- Chaque TP est **mesuré** : benchmark, profiling, comparaison chiffrée
- L'accent est mis sur la **compréhension des mécanismes**, pas la mémorisation d'API

---

## Outils utilisés dans le curriculum

| Outil | Usage | Cours |
|-------|-------|-------|
| CMake | Build system | Tous |
| RenderDoc | GPU debugging | 05, 06, 07, 13 |
| Nsight / PIX | GPU profiling | 06, 07, 08 |
| Tracy | CPU profiling | 09, 11, 12 |
| Dear ImGui | UI d'éditeur | 11 |
| assimp | Chargement modèles | 11 |
| GLAD | Chargement OpenGL | 05 |
| VMA | Allocation Vulkan | 06 |
| sol2 | Binding Lua | 11 |
| stb_image / stb_vorbis | Chargement assets | 02, 10 |
| glslang / shaderc | Compilation shaders | 04, 06 |
| SPIRV-Cross | Cross-compilation | 04 |
| OpenXR | XR standard | 16, 17 |
| NkWindow | Fenêtrage custom | Tous |

---

## Évaluation globale

Chaque cours est évalué sur :
- **TP hebdomadaires (40%)** : fonctionnalité + performance mesurée
- **Projet final (40%)** : intégration de toutes les compétences du cours
- **Rapport technique (20%)** : documentation, analyse, comparaisons

Le cours 18 remplace les évaluations individuelles pour une note de capstone globale.
