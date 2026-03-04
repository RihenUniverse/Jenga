# Cours 17 — XR Programming from scratch
**Prérequis :** Cours 15 (AR), 16 (VR), 13 (rendu avancé)  
**Durée estimée :** 8 semaines  
**Objectif :** Unifier AR et VR dans un framework XR cohérent, implémenter le Mixed Reality (passthrough), et maîtriser les cas d'usage avancés comme les hologrammes spatiaux.

---

## Unité 1 — Architecture XR unifiée (1 semaine)

### Semaine 1
- Spectre XR : Reality-Virtuality Continuum de Milgram
- Passthrough camera AR (Quest, HoloLens) vs optical see-through (HoloLens, Magic Leap)
- Architecture unifiée : système de tracking commun, renderer commun, input abstrait
- Conception du framework `NkXR` : `XRSession`, `XRFrame`, `XRView`, `XRSpace`
- XR modes : VR, AR, MR, passthrough — switching dynamique
- **TP :** Framework XR squelette avec mode switch VR/AR at runtime

---

## Unité 2 — Mixed Reality et Passthrough (2 semaines)

### Semaine 2
- Passthrough rendering : flux caméra aligné sur les yeux, latence minimale
- Distorsion de passthrough : correction pour les lentilles de Fresnel
- Depth compositing : Z-buffer mixé réel/virtuel
- Scene understanding : détection de surfaces (planes, meshes) en temps réel
- Spatial anchors : points d'ancrage persistants dans l'espace réel
- **TP :** Application MR : objets virtuels occultés par des mains réelles, ancrés dans l'espace

### Semaine 3
- World mesh reconstruction : reconstruction dense de l'environnement
- Collision avec la géométrie réelle : objets virtuels qui rebondissent sur les murs réels
- Semantic segmentation pour l'occlusion fine (ML sur le depth stream)
- Lighting estimation avancée : reconstruction d'une sonde d'environnement depuis les caméras
- Dynamic lighting from real environment
- **TP :** Simulation physique de billes virtuelles interagissant avec des surfaces réelles

---

## Unité 3 — Hologrammes spatiaux et rendu avancé XR (2 semaines)

### Semaine 4
- Rendu d'hologrammes stables : stabilisation par plane projection
- LSR (Late Stage Reprojection) spécifique XR : depth submission, plane hint
- Spatial sound : HRTF binaurale alignée sur le tracking de tête
- Object anchoring : tracker un objet réel et y attacher du contenu virtuel
- Reconnaître des objets réels (modèle ML embarqué) pour l'interaction
- **TP :** Hologramme stable sur un objet réel reconnu, son 3D spatialisé

### Semaine 5
- Rendu volumétrique pour XR : hologrammes en "3D réel" (light field concept)
- Holographic Display basics : barrière de parallaxe, lenticular lens (théorie)
- Hand tracking avancé : MediaPipe-like from scratch pour 21 keypoints
- Pinch gestures, palm facing, finger counting — recognition
- Near-field interaction : UI 3D manipulée directement avec les doigts
- **TP :** Interface XR entièrement contrôlée par les mains, sans contrôleur

---

## Unité 4 — Collaboration multi-utilisateurs en XR (2 semaines)

### Semaine 6
- Shared spaces : référentiel commun entre plusieurs utilisateurs
- Synchronisation de pose : serveur de coordination, consensus de repère
- Shared anchors : ancres spatiales partagées via un serveur
- Avatar XR : représentation des autres utilisateurs dans l'espace partagé
- Late join : rejoindre une session active avec l'état courant

### Semaine 7
- Synchronisation d'état : CRDT (Conflict-free Replicated Data Type) pour les objets partagés
- Networking XR : tolérance à la latence, prediction, interpolation
- Audio spatialisé multi-utilisateurs : voix des avatars positionnés dans l'espace
- Gestion des conflits d'interaction : qui peut saisir un objet
- **TP :** Expérience XR collaborative à 2 utilisateurs : co-édition de scène 3D partagée

---

## Unité 5 — Cas d'usage industriels et avancés (1 semaine)

### Semaine 8
- XR pour la formation industrielle : assemblage guidé, instructions AR overlay
- Jumeau numérique (digital twin) : synchronisation modèle 3D ↔ objet réel
- Télé-présence XR : streaming de présence 3D
- Privacy et sécurité en XR : protections des données spatiales, eye tracking
- Performance sur hardware embarqué : optimisations spécifiques Snapdragon XR
- **TP :** Application de formation : montage d'un objet guidé par instructions AR avec détection d'erreurs

---

## Projet Final

**Expérience XR hybride AR/VR** :
- Switching dynamique entre mode VR et mode AR/MR
- World mesh collision
- Hand tracking sans contrôleur
- Multi-utilisateurs (2+) dans le même espace partagé
- Audio 3D spatialisé
- Contenu ancré dans l'espace réel (spatial anchors)
- 72fps+ stable sur headset embarqué

**Rapport :** Comparaison de l'architecture avec HoloLens 2 SDK et Meta XR SDK.
