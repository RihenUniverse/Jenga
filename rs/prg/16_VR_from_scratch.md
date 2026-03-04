# Cours 16 — VR Programming from scratch
**Prérequis :** Cours 01, 05 ou 06, 12, 13  
**Durée estimée :** 10 semaines  
**Objectif :** Implémenter tous les mécanismes d'un système VR from scratch : stéréoscopie, head tracking, rendu optimisé, interaction, confort.

---

## Unité 1 — Perception visuelle et stéréoscopie (2 semaines)

### Semaine 1
- Perception humaine de la profondeur : indices monoculaires et binoculaires
- Disparité stéréoscopique : IPD (Inter-Pupillary Distance), vergence
- Vergence-accommodation conflict : cause principale du mal des transports
- Modèle optique d'un casque VR : lentilles de Fresnel, distorsion radiale
- Calcul du FOV (Field of View) asymétrique par œil
- Matrices de projection VR : projection asymétrique, near/far per eye
- **TP :** Rendu stéréoscopique sur un écran avec separation couleur (anaglyphe), puis side-by-side

### Semaine 2
- Lens distortion correction from scratch : distorsion de barillet et correction inverse
- Chromatic aberration correction : offsets RGB différents pour les lentilles
- Foveated rendering concept : zone centrale haute résolution, périphérie dégradée
- Fixed Foveated Rendering : implémentation par zones dans le shader
- Eye-tracked foveated rendering (concept, si matériel disponible)
- Reprojection : extrapoler une frame manquée pour réduire la latence perçue
- **TP :** Renderer VR software avec lens distortion correcte pour Cardboard

---

## Unité 2 — Head Tracking et Orientation (2 semaines)

### Semaine 3
- IMU (Inertial Measurement Unit) : accéléromètre, gyroscope, magnétomètre
- Integration du gyroscope : drift, biais
- Complémentary filter from scratch : fusion gyro + accel
- Filtre de Madgwick from scratch : gradient descent sur quaternions
- Filtre de Kalman Étendu (EKF) pour la fusion 9-DOF
- **TP :** Orientation tracking from scratch avec un module IMU réel ou données simulées

### Semaine 4
- Positional tracking 6-DOF : nécessité des caméras
- Inside-out tracking : caméras embarquées sur le casque (Quest style)
- Optical flow + IMU fusion pour le tracking de position
- Room-scale boundaries : définition de l'espace de jeu, alertes de proximité
- Tracking de manettes : IR leds, optical tracking basique
- **TP :** Simulateur de tracking 6-DOF avec données synthétiques, visualisation de la pose

---

## Unité 3 — Rendu VR haute performance (2 semaines)

### Semaine 5
- Single Pass Stereo rendering : instanciation GPU pour les deux yeux
- Multi-View Rendering (MVR) : extension OpenGL `GL_OVR_multiview`
- Render to texture per eye + final blit avec distortion shader
- Late Latency Reduction : async timewarp / reprojection
- Asynchronous Reprojection from scratch : warping d'une frame existante
- **TP :** Pipeline VR complet : single pass stereo + distortion + reprojection

### Semaine 6
- VR rendering budget : 90Hz = 11.1ms, 120Hz = 8.3ms
- Fixed Foveated Rendering implémentation GPU (Vulkan/OpenGL)
- Variable Rate Shading pour VR
- Optimisation des draw calls : batching agressif
- VR-specific LOD : LOD plus agressif en périphérie
- Thermal throttling sur mobile (Quest) : gestion du budget thermique
- **TP :** Scène VR à 90fps stable avec 200 objets, profiling per-eye

---

## Unité 4 — Interaction VR (2 semaines)

### Semaine 7
- Interaction 3D : ray casting depuis le contrôleur
- Grabbing d'objets : attachement, contraintes physiques
- Hand presence : modèle de main, IK pour les doigts
- Haptic feedback : patterns de vibration, encodage de la force
- Locomotion : teleportation (arc parabolique), smooth locomotion, dash
- **TP :** Sandbox VR : attraper, lancer, interagir avec des objets physiques

### Semaine 8
- UI en VR : monde-attaché vs tête-attachée vs main-attachée
- Interaction avec des panneaux 2D en espace 3D
- Keyboard VR : layout circulaire, raycast selection
- Confort et accessibilité : options de réduction du mal des transports
- Social VR basique : représentation avatar, synchronisation réseau
- **TP :** Menu VR complet interactif avec barre de santé, inventaire, settings

---

## Unité 5 — Confort et physiologie (1 semaine)

### Semaine 9
- Simulator sickness : causes (latence, FOV, accord vergence/accommodation)
- Métriques de confort : latence totale (motion-to-photon), frame rate stability
- Mesure du motion-to-photon latency
- Techniques de réduction de la cybercinétose :
  - Vignette dynamique lors des déplacements
  - Réduction du FOV dynamique
  - Point de stabilité (stable reference point)
- Guidelines de design VR : Google, Oculus Best Practices
- **TP :** Implémenter les 3 techniques de réduction de cybercinétose, évaluation subjective

---

## Unité 6 — Intégration OpenXR (1 semaine)

### Semaine 10
- OpenXR : standard cross-platform (Meta, Valve, Microsoft)
- `XrInstance`, `XrSession`, `XrSwapchain`, `XrSpace`
- Input abstraction OpenXR : action sets, bindings
- Rendering loop OpenXR : `xrWaitFrame`, `xrBeginFrame`, `xrEndFrame`
- Comparaison implémentation from scratch vs OpenXR
- **TP :** Porter le renderer VR du cours sur OpenXR, tester sur Quest/PCVR

---

## Projet Final

**Application VR complète** :
- Tracking 6-DOF (OpenXR ou simulation)
- Single pass stereo rendering
- Lens distortion correction
- Reprojection asynchrone
- Interaction physique avec les mains
- Locomotion confortable
- UI 3D
- 90fps stable en 2K per eye
- Rapport de latence motion-to-photon mesuré

**Critère :** Aucun frame drop sur 5 minutes d'utilisation continue, latence < 20ms.
