# Cours 15 — AR Programming from scratch
**Prérequis :** Cours 01, 03, 05, 14 (vision par ordinateur)  
**Durée estimée :** 10 semaines  
**Objectif :** Implémenter un système de Réalité Augmentée complet en C++, sans ARCore/ARKit, en comprenant chaque mécanisme : tracking, calibration, rendu hybride.

---

## Unité 1 — Vision par ordinateur fondamentale (2 semaines)

### Semaine 1
- Modèle de caméra sténopé (pinhole) : focal length, centre optique, distorsion
- Matrice intrinsèque K : fx, fy, cx, cy
- Calibration de caméra : échiquier, équations de correspondance
- Algorithme de calibration de Zhang from scratch : DLT, raffinement LM
- Coefficients de distorsion radiale et tangentielle
- Rectification d'image : undistort from scratch (remapping bilinéaire)
- **TP :** Calibrer une webcam avec un échiquier, undistort les images en temps réel

### Semaine 2
- Détection de features 2D :
  - Harris Corner Detector from scratch
  - FAST (Features from Accelerated Segment Test)
  - ORB (Oriented FAST and Rotated BRIEF) from scratch
- Descripteurs : BRIEF, ORB descriptors — implémentation binaire
- Matching de features : brute force + Lowe's ratio test
- Homographie : DLT algorithm, RANSAC from scratch
- **TP :** Tracking planaire par homographie + RANSAC, overlay d'une image sur un plan

---

## Unité 2 — Pose estimation (2 semaines)

### Semaine 3
- PnP (Perspective-n-Point) : trouver R,t depuis N correspondances 3D-2D
- EPnP algorithm from scratch
- Reprojection error : mesure de la qualité de pose
- RANSAC pour PnP : filtrage des outliers
- Marker-based tracking : QR codes, ArUco markers — décodage from scratch
- **TP :** Tracker un marker ArUco, afficher un cube 3D dessus, ≤ 2° d'erreur angulaire

### Semaine 4
- SfM (Structure from Motion) basique : 2 vues → reconstruction 3D
- Matrice fondamentale F et matrice essentielle E : 8-point algorithm
- Décomposition de E → R,t (4 solutions, choix par cheirality)
- Triangulation : DLT linéaire, optimisation non-linéaire
- Épipolar geometry : visualisation des lignes épipolaires
- **TP :** Reconstruction 3D de 2 photos d'une scène, nuage de points visualisé

---

## Unité 3 — SLAM (Simultaneous Localization And Mapping) (3 semaines)

### Semaine 5
- SLAM problem : localisation et cartographie simultanées
- Feature-based SLAM : front-end tracking + back-end optimisation
- Optical flow : Lucas-Kanade pyramidal from scratch
- Keyframe selection : disparité, angle de rotation
- Map points : création, fusion, culling

### Semaine 6
- Graph-based SLAM : pose graph, facteurs de contrainte
- Bundle adjustment : optimisation non-linéaire de pose + structure (LM / GN)
- Levenberg-Marquardt from scratch pour bundle adjustment
- Loop closure detection : bag-of-words (DBoW2 concept), place recognition
- Global map correction après loop closure

### Semaine 7
- SLAM dense vs épars
- Dense depth estimation : stereo matching (SGM — Semi-Global Matching simplifié)
- Plane detection : RANSAC sur le nuage de points
- Surface reconstruction : marching cubes simplifié
- Fusion volumétrique : TSDF (Truncated Signed Distance Function)
- **TP :** Mini-SLAM monoculaire fonctionnel sur séquence vidéo TUM dataset

---

## Unité 4 — Rendu AR (2 semaines)

### Semaine 8
- AR rendering pipeline : frame caméra + rendu 3D aligné
- Occlusion handling : depth test contre la géométrie réelle
- Lighting estimation : estimation de la couleur et direction de la lumière ambiante depuis l'image
- Environment probes : cube map de l'environnement réel pour IBL
- Shadow casting sur des surfaces réelles : shadow receiver virtuel
- **TP :** Objet 3D PBR placé sur une surface réelle, ombres correctes

### Semaine 9
- Latency compensation : prediction du pose pour le prochain frame
- Rolling shutter correction : modèle de distorsion temporelle
- IMU integration : filtre complémentaire accéléromètre + gyroscope
- Sensor fusion : EKF (Extended Kalman Filter) pour fusion IMU + vision from scratch
- **TP :** EKF de fusion IMU/vision from scratch, test sur données synthétiques

---

## Unité 5 — Expériences AR avancées (1 semaine)

### Semaine 10
- Détection et suivi d'objets 3D (modèle-based tracking)
- Segmentation d'image en temps réel pour l'occlusion fine
- Hands tracking from scratch : détection de keypoints de la main
- Face tracking : landmarks faciaux, masques AR
- **TP :** Application AR complète : poser un meuble virtuel dans une pièce réelle, ombres, occlusion

---

## Projet Final

**Système AR monoculaire complet** :
- Calibration de caméra intégrée
- SLAM monoculaire (sparse)
- Détection de plans horizontaux
- Placement d'objets 3D sur les plans
- Rendu PBR avec lighting estimation
- Occlusion par la géométrie réelle
- 30fps sur webcam standard

**Rapport :** Précision de tracking (RMSE sur trajectoire), comparaison avec ARCore.
