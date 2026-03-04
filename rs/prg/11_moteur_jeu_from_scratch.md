# Cours 11 — Moteurs de Jeu from scratch
**Prérequis :** Cours 01–05, 09, 10  
**Durée estimée :** 14 semaines  
**Objectif :** Concevoir et implémenter un moteur de jeu complet en C++, de l'architecture système à l'outil d'édition, sans Unity/Unreal.

---

## Unité 1 — Architecture d'un moteur (2 semaines)

### Semaine 1
- Anatomie d'un moteur : core, renderer, physics, audio, input, scripting, editor
- Boucle de jeu : fixed update vs variable update, frame pacing
- Timer haute résolution : `QueryPerformanceCounter`, horloge monotonique
- Gestion de la mémoire : allocateurs custom (linear, pool, stack, heap) — aucun `new/delete` dans le hot path
- Module system : dépendances, initialisation ordonnée, shutdown propre
- **TP :** Squelette du moteur : boucle de jeu, timer, allocateurs, logging

### Semaine 2
- Entity Component System (ECS) from scratch :
  - Archetype-based ECS : storage dense par archetype
  - `Entity` = ID (generation + index), `Component` = données pures, `System` = logique
  - Queries : itération efficace sur les archétypes correspondants
- Comparison ECS vs OOP classique : cache friendliness
- Serialisation des entités : format binaire custom et JSON
- **TP :** ECS complet avec 100 000 entités : transform, velocity, render component — benchmark

---

## Unité 2 — Gestion des ressources (2 semaines)

### Semaine 3
- Asset pipeline : formats sources → formats runtime (offline cooking)
- Asset manager : chargement asynchrone, cache par GUID, reference counting
- Hot-reloading des assets : watch sur les fichiers, rechargement transparent
- Format de mesh runtime : positions, normales, UVs, indices — interleaved vs planar
- Format de texture runtime : compression BC7/DXT, mipmaps pré-générés
- **TP :** Asset manager complet avec hot-reload de textures et shaders

### Semaine 4
- Animations squelettiques : skeleton (hiérarchie d'os), pose, clip d'animation
- Format d'animation : lecture de FBX simplifié via assimp ou format custom
- Skinning CPU et GPU (compute shader)
- Animation blending : LERP de poses, state machine d'animation (from scratch)
- Inverse kinematics basique : FABRIK algorithm
- **TP :** Personnage animé avec state machine (idle/walk/run/jump) et IK pour les pieds

---

## Unité 3 — Physique from scratch (3 semaines)

### Semaine 5
- Rigidbody dynamics : masse, forces, intégration de Verlet
- Collision detection broad phase : AABB tree (BVH), Sweep And Prune (SAP)
- Narrow phase : GJK algorithm (Gilbert-Johnson-Keerthi) + EPA (Expanding Polytope Algorithm)
- Collision response : impulsion, restitution, friction de Coulomb
- **TP :** Simulation de 500 boîtes qui tombent et rebondissent, 60fps

### Semaine 6
- Contraintes et joints : distance constraint, hinge, ball-socket
- Position Based Dynamics (PBD) : simulation de tissu, soft bodies
- Trigger volumes : overlap queries sans résolution de collision
- Raycasting et shapecasting dans la scène physique
- Sleeping : désactivation des corps immobiles
- **TP :** Ragdoll physique avec joints, simulation d'un personnage qui tombe

### Semaine 7
- Physique des véhicules : suspension (raycasting contre le sol), moteur, friction des pneus
- Simulation de fluides 2D basique (pour effets)
- Debugging de la physique : visualisation des colliders, forces, joints
- Intégration physique/rendu : synchronisation des transforms
- **TP :** Véhicule jouable avec physique correcte sur terrain irrégulier

---

## Unité 4 — Systèmes de jeu (3 semaines)

### Semaine 8
- Scripting système : interface C++ exposée à un langage de script (Lua via sol2)
- Binding automatique : macros de réflexion, `REFLECT_CLASS`, `REFLECT_METHOD`
- Hot-reload de scripts Lua
- Event system : publisher/subscriber, priorités, filtrage
- **TP :** Exposer l'ECS à Lua, script de comportement d'ennemi en Lua

### Semaine 9
- Navigation et pathfinding : NavMesh generation (Recast simplifié), A* sur le NavMesh
- Steering behaviors : seek, flee, arrive, pursue, obstacle avoidance
- AI perception : vision cone, ouïe, mémoire des percepts
- Behavior Trees from scratch : selector, sequence, decorator, leaf tasks
- **TP :** IA ennemie avec BT : patrouille, détection, poursuite, attaque

### Semaine 10
- Network : architecture client/server, UDP avec reliability layer
- Snapshot interpolation : état du serveur → rendu client interpolé
- Lag compensation : rollback netcode basique
- Lobby et matchmaking simplifié
- **TP :** Jeu multi-joueur simple (shooteur top-down 2 joueurs) over LAN

---

## Unité 5 — Éditeur de scène (2 semaines)

### Semaine 11
- Immediate mode GUI from scratch : rendu de widgets sur le framebuffer
- Alternative : intégration de Dear ImGui (seule bibliothèque externe autorisée ici)
- Scene hierarchy panel : affichage de l'arbre d'entités
- Inspector panel : édition des composants, type reflection pour auto-generated UI
- Asset browser : thumbnail preview, drag-and-drop

### Semaine 12
- Gizmos 3D : translation, rotation, scale — interaction souris
- Undo/redo : command pattern, history stack
- Play mode / editor mode : sauvegarde et restauration de l'état
- Scene serialisation : JSON ou format binaire
- **TP :** Éditeur fonctionnel : créer une scène, placer des objets, tester in-editor

---

## Unité 6 — Intégration et polish (2 semaines)

### Semaine 13 — Intégration complète
- Intégration du moteur audio (cours 10)
- Intégration de l'input system (NkWindow)
- Build system cross-platform : CMake, presets
- Packaging : génération d'un exécutable + assets compressés

### Semaine 14 — Optimisation et finalisation
- Profiling de la frame complète : CPU + GPU
- Multi-threading de la mise à jour ECS, du culling, du render submission
- Load time optimization : async loading, cache warming
- **TP :** Démo jouable : mini-jeu 3D complet avec IA, physique, audio

---

## Projet Final

**Moteur de jeu complet** avec une démo jouable :
- ECS archetypes, 100 000+ entités
- Physique rigidbody + PBD
- Animations squelettiques + IK
- IA avec Behavior Trees
- Audio 3D
- Éditeur de scène avec undo/redo
- 60fps en 1080p

**Livrable :** Code source + exécutable + documentation architecture.
