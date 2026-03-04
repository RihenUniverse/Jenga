# Cours 12 — Realtime Systems Programming
**Prérequis :** Cours 09, 11, C++ avancé  
**Durée estimée :** 8 semaines  
**Objectif :** Maîtriser la programmation de systèmes temps réel stricts : scheduling, latence déterministe, multi-threading avancé, et design de boucles de jeu professionnelles.

---

## Unité 1 — Temps réel : définitions et contraintes (1 semaine)

### Semaine 1
- Temps réel strict (hard) vs souple (soft) : définitions, critères
- Sources de non-déterminisme : GC, allocations, system calls, I/O
- OS scheduling : priorités de threads, real-time scheduling (`SCHED_FIFO`, `SetThreadPriority`)
- Affinité CPU : `SetThreadAffinityMask`, isolation de cœurs
- Tick rate vs frame rate : update fixe 60Hz vs rendu variable
- Frame pacing : mesure du jitter, détection des spikes
- **TP :** Mesurer et histogrammer le jitter de la boucle principale, identifier les sources

---

## Unité 2 — Job Systems et task-based parallelism (2 semaines)

### Semaine 2
- Thread pool from scratch : worker threads, task queue lock-free
- Work stealing : algorithme de Chase-Lev deque
- Dependencies entre tâches : DAG d'exécution, barrières
- Fibers (co-routines légères) : context switching manuel
- Fiber-based job system (architecture Naughty Dog) : task scheduler sans OS threads
- **TP :** Job system fiber-based, benchmark vs thread pool classique

### Semaine 3
- Frame graph (Render Graph) : description déclarative du pipeline de rendu
- Analyse des dépendances, topological sort
- Allocation automatique des ressources transientes
- Parallélisation automatique des passes indépendantes
- Dry-run mode : validation sans exécution GPU
- **TP :** Render graph complet avec 6 passes : shadow, G-buffer, lighting, SSAO, bloom, final

---

## Unité 3 — Structures de données lock-free (2 semaines)

### Semaine 4
- Modèle mémoire C++ 11 : `std::atomic`, ordres (relaxed, acquire, release, seq_cst)
- ABA problem : version counters, hazard pointers
- Lock-free queue SPSC (Single Producer Single Consumer) : ring buffer atomique
- Lock-free queue MPMC (Multi Producer Multi Consumer) : algorithme de Michael-Scott
- Lock-free stack : Treiber stack

### Semaine 5
- Hazard pointers : libération sûre de mémoire sans GC
- Epoch-based reclamation
- RCU (Read-Copy-Update) : lectures sans lock, mise à jour par copie
- Cas pratique : asset manager thread-safe avec RCU
- Double-buffered state : producer/consumer de données par swap de buffers
- **TP :** Comparaison de performances : mutex vs lock-free MPMC queue sous charge

---

## Unité 4 — Mémoire et allocateurs temps réel (1 semaine)

### Semaine 6
- Problèmes des allocateurs génériques (`malloc/free`) en temps réel
- Linear allocator (bump allocator) : allocation O(1), reset par frame
- Pool allocator : blocs de taille fixe, O(1) alloc/free
- Stack allocator avec markers
- TLSF (Two-Level Segregated Fit) : allocateur général O(1)
- Memory tagging : tracking par système pour détecter les leaks
- **TP :** Remplacer tous les allocateurs d'un système de particules, zéro spike de mémoire

---

## Unité 5 — Simulation et interpolation (1 semaine)

### Semaine 7
- Fixed timestep + variable rendering : "Fix Your Timestep!" (Glenn Fiedler)
- Accumulator pattern : découplage simulation/rendu
- State interpolation : LERP entre t et t+dt pour le rendu
- Rollback netcode from scratch : save state, restore state, re-simulate
- Input delay vs rollback : trade-offs pour le multi-joueur
- **TP :** Simulation physique à 120Hz, rendu à 60fps avec interpolation — aucun stutter visible

---

## Unité 6 — Profiling et debugging de systèmes (1 semaine)

### Semaine 8
- Instrumentation manuelle : `__rdtsc`, macros de scope timer
- Tracy profiler : intégration, zones, frames, plots, messages
- Détection des spikes : alerts sur dépassement de budget
- Visualisation de la frame : gantt chart des tâches parallèles
- Memory usage tracking : peak, fragmentation, par catégorie
- **TP :** Instrumenter le moteur du cours 11 avec Tracy, produire une analyse de frame complète

---

## Projet Final

**Boucle de jeu temps réel déterministe** :
- Job system fiber-based
- Render graph avec parallélisation automatique
- Simulation fixe 120Hz + rendu 60fps avec interpolation
- Zéro allocation dans le hot path
- Frame budget : 16.6ms max, p99 < 18ms (mesuré sur 60 secondes)
- Rapport Tracy documenté avec analyse de toutes les tâches

**Critère :** Aucun frame spike > 1ms au-dessus du budget sur 10 000 frames consécutives.
