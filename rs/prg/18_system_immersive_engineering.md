# Cours 18 — System & Immersive Engineering (Capstone)
**Prérequis :** Tous les cours précédents (ou au moins 11, 12, 13, 14, et un de 15/16/17)  
**Durée estimée :** 12 semaines  
**Objectif :** Intégrer tous les systèmes dans un framework de production, concevoir une architecture modulaire robuste, et livrer une expérience immersive complète de qualité professionnelle.

---

## Unité 1 — Architecture de systèmes complexes (2 semaines)

### Semaine 1
- Patterns d'architecture pour les moteurs et systèmes immersifs :
  - Layered architecture : plateforme → core → engine → application
  - Plugin architecture : discovery, loading dynamique, versioning
  - Service locator vs dependency injection
  - Event-driven architecture : bus d'événements global, ordering, filtering
- Gestion des dépendances circulaires : techniques de découplage
- API design : principes SOLID appliqués à un moteur
- **TP :** Audit de l'architecture du cours 11, refactoring vers une architecture layered propre

### Semaine 2
- Cross-platform abstraction : couche HAL (Hardware Abstraction Layer)
- Feature detection runtime : capabilities GPU, VR hardware, IMU disponible
- Graceful degradation : fallbacks automatiques (VR → écran, RT → rasterization)
- Configuration system : fichiers de config, validation, hot-reload
- Telemetry et analytics intégrés : métriques de performance, crash reporting
- **TP :** HAL complet : même code applicatif tourne sur PC desktop + simulateur mobile

---

## Unité 2 — Pipeline de build et devops (1 semaine)

### Semaine 3
- CMake avancé : presets, toolchains cross-compilation, find_package custom
- CI/CD pour un projet C++ : GitHub Actions, build matrix (Windows/Linux/Mac)
- Tests automatisés : unit tests (Catch2), integration tests, screenshot comparison
- Asset pipeline automatisé : preprocessing au build time
- Packaging et distribution : installeur, mise à jour delta
- **TP :** Pipeline CI complet : build + tests + packaging automatisé sur 3 plateformes

---

## Unité 3 — Systèmes de production (2 semaines)

### Semaine 4
- Gestion des erreurs robuste : error codes vs exceptions, error propagation
- Système de logging de production : niveaux, sinks (fichier, réseau, console), rotation
- Crash reporting : minidumps Windows, stack unwinding, symbolication
- Watchdog system : détection de freeze, redémarrage automatique
- Monitoring de performance en production : métriques temps réel vers un dashboard

### Semaine 5
- Serialisation robuste : versioning de format, migration de données, rétrocompatibilité
- Base de données embarquée : SQLite pour les saves, les préférences
- Encryption et sécurité : protection des sauvegardes, anti-cheat basique
- Privacy par design : GDPR compliance, anonymisation des données
- Update system : hot patches, DLC streaming
- **TP :** Système de sauvegarde versionné avec migration automatique, chiffrement

---

## Unité 4 — Intégration complète des systèmes (3 semaines)

### Semaine 6 — Intégration Rendu + IA
- Intégration du renderer avancé (cours 13) dans le moteur (cours 11)
- IA embarquée : modèles d'inférence dans le pipeline de rendu
- Neural rendering : DLSS-like upscaling basique avec le réseau du cours 14
- Génération procédurale IA : terrain, objets, textures

### Semaine 7 — Intégration XR
- Intégration du framework XR (cours 17) dans le moteur
- XR renderer hook : remplacement du backend rendu standard par le pipeline XR
- Input abstraction : manettes standards + hand tracking + gaze + voice
- Spatial audio integration : moteur audio (cours 10) + spatialisation HRTF

### Semaine 8 — Intégration réseau et cloud
- Backend cloud minimal : game server autorité, REST API pour les scores
- LiveOps infrastructure : configuration à distance, feature flags
- Streaming de contenu : assets chargés depuis le réseau à la demande
- Persistence de monde XR partagé : anchres serveur, persistance entre sessions
- **TP :** Expérience XR multi-joueurs avec persistence entre sessions

---

## Unité 5 — Optimisation système complète (2 semaines)

### Semaine 9
- Profiling de l'intégration : bottlenecks d'architecture (pas juste de code)
- Memory layout global : éviter la fragmentation inter-systèmes
- Startup time optimization : lazy initialization, parallel loading
- Shutdown propre : ordre de destruction, leaks détection, rapport final

### Semaine 10
- Budget management global : CPU, GPU, RAM, VRAM, stockage, réseau, batterie
- Adaptive quality system : réduire/augmenter qualité selon les budgets disponibles
- Power management : réduction de fréquence GPU en scènes simples
- Thermal management : throttling progressif avec notification à l'application
- **TP :** Adaptive quality system qui maintient 60fps en ajustant automatiquement résolution et effets

---

## Unité 6 — Projet Capstone (2 semaines)

### Semaine 11 et 12 — Réalisation du projet final

Le projet final intègre **au minimum** :
- Le moteur de jeu complet (cours 11)
- Le renderer avancé (cours 13)
- Un système XR/VR/AR (cours 15/16/17)
- L'IA (cours 14) intégrée dans le gameplay
- L'audio 3D (cours 10)
- Le networking multi-joueurs
- L'éditeur de scène
- Le pipeline CI/CD

**Thèmes proposés** (ou libre) :

**Option A : Expérience VR de formation industrielle**
- Simulation d'une ligne d'assemblage
- Instructions AR overlay guidées par IA
- Multi-utilisateurs : formateur + stagiaire
- Analytics : suivi des erreurs, temps par étape

**Option B : Jeu XR hybride AR/VR**
- Bascule AR (monde réel comme terrain de jeu) ↔ VR (monde fantaisie)
- IA ennemis adaptatifs (RL)
- Multi-joueurs cross-platform (desktop + headset)
- Économie virtuelle persistante

**Option C : Jumeau numérique interactif**
- Scan 3D d'une salle (SLAM)
- Simulation physique d'objets virtuels dans l'espace réel
- Monitoring de capteurs IoT en AR
- Collaboration multi-utilisateurs

---

## Évaluation finale

**Livrable technique :**
- Code source complet, documenté, tests unitaires
- Pipeline CI/CD fonctionnel
- Build reproductible sur Windows + Linux
- README de build et d'utilisation

**Rapport technique (20 pages minimum) :**
- Architecture globale avec diagrammes
- Décisions de conception justifiées
- Analyse de performance (profiling CPU + GPU)
- Problèmes rencontrés et solutions
- Comparaison avec les solutions industrielles (Unity, Unreal, OpenXR SDK)

**Présentation orale (30 minutes) :**
- Démo live de l'expérience
- Explication d'un sous-système au choix en détail
- Questions des évaluateurs

**Critères de note :**
- Fonctionnalité et robustesse (30%)
- Qualité du code et de l'architecture (25%)
- Performance mesurée (20%)
- Innovation et profondeur technique (15%)
- Documentation et présentation (10%)
