# Cours 09 — Optimisation & Performance
**Prérequis :** Cours 01–08 (ou au moins 01, 03, 05)  
**Durée estimée :** 8 semaines  
**Objectif :** Maîtriser les techniques d'optimisation CPU et GPU, développer une méthodologie rigoureuse basée sur la mesure avant l'intuition.

---

## Unité 1 — Méthodologie et mesure (1 semaine)

### Semaine 1
- **Règle fondamentale : ne jamais optimiser sans mesurer**
- Profiling CPU : `gprof`, `perf` (Linux), Very Sleepy / VTune (Windows)
- Flame graphs : interprétation, identification des hot paths
- Compteurs hardware : cycles, IPC, cache misses, branch mispredictions
- Microbenchmarking : `std::chrono`, Google Benchmark, pièges (warmup, outliers)
- Profiling GPU : RenderDoc, Nsight, PIX — frame time vs CPU time
- **TP :** Profiler le renderer du cours 03 ou 05, produire un rapport de bottlenecks

---

## Unité 2 — Optimisation CPU : mémoire et cache (2 semaines)

### Semaine 2
- Hiérarchie mémoire : L1/L2/L3 cache, RAM — latences en cycles
- Cache line : 64 bytes, false sharing en multi-threading
- Data-Oriented Design (DOD) : AoS (Array of Structs) vs SoA (Struct of Arrays)
- Cache-friendly traversal : accès séquentiel vs aléatoire, padding vs compactness
- `__builtin_prefetch` / `_mm_prefetch` : prefetching manuel
- **TP :** Réécrire un système de particules AoS → SoA, mesurer le speedup (cache miss rate)

### Semaine 3
- SIMD (Single Instruction Multiple Data) :
  - SSE2 : 128 bits, 4 floats en parallèle
  - AVX2 : 256 bits, 8 floats en parallèle
  - AVX-512 : 512 bits, 16 floats en parallèle
- Intrinsics C++ : `_mm256_add_ps`, `_mm256_mul_ps`, `_mm256_load_ps`
- Auto-vectorisation du compilateur : flags (`-O3 -march=native`), hints
- Alignement mémoire : `alignas(32)`, `_mm_malloc`
- **TP :** Transformation de 1M de vecteurs : scalaire vs SSE2 vs AVX2, mesure du speedup

---

## Unité 3 — Optimisation CPU : algorithmes et branches (1 semaine)

### Semaine 4
- Complexité algorithmique vs constantes cachées
- Branch prediction : pipelines CPU, coût d'un misprediction
- Branchless programming : `cmov`, `?:` hint, lookup tables
- Inlining, devirtualization, PGO (Profile-Guided Optimization)
- Link-time optimization (LTO) : `-flto`
- Allocation mémoire : arènes (arena allocator), pool allocator, stack allocator from scratch
- **TP :** Pool allocator for game objects vs `new/delete`, mesure throughput

---

## Unité 4 — Optimisation multi-threading (1 semaine)

### Semaine 5
- Concurrence vs parallélisme
- False sharing : isolation par padding de cache line
- Lock-free structures : atomic operations, compare-and-swap
- Job system from scratch : work stealing queue, fiber-based scheduling
- Task-based parallelism : décomposition de la frame en tâches
- **TP :** Job system qui parallélise le frustum culling et la mise à jour des transforms, mesure du scaling sur N cores

---

## Unité 5 — Optimisation GPU (2 semaines)

### Semaine 6
- Bottlenecks GPU : vertex-bound, fragment-bound, bandwidth-bound, compute-bound
- Diagnostic avec les outils : GPU occupancy, wave/warp utilisation
- Optimisation des vertex shaders : réduction des attributs, instancing
- Optimisation des fragment shaders : early Z, coût des `discard`, branchements
- Bandwidth : compression de textures (BC7, ASTC), tiling, render target formats
- **TP :** Profiler un shader lourd, identifier et corriger le bottleneck principal

### Semaine 7
- GPU occupancy : registres, shared memory, nombre de warps actifs
- Draw call reduction : instancing, indirect drawing, batching de matériaux
- Occlusion culling : hardware occlusion queries, Hi-Z culling
- Tile-based deferred rendering (TBDR) pour mobile
- Shader permutations vs dynamic branching : trade-offs
- **TP :** Réduire de 10 000 draw calls à < 100 en GPU-driven rendering

---

## Unité 6 — Optimisation de systèmes complets (1 semaine)

### Semaine 8
- Frame pacing et synchronisation : vsync, frame cap, jitter
- Streaming d'assets : chargement asynchrone, budget de stall
- Compression de données : LZ4, Zstd pour les assets, impact sur le chargement
- Memory budgets : VRAM, RAM — tracking et alertes
- Optimisation pour différentes plateformes : PC, mobile, consoles
- **TP :** Optimiser le moteur du projet final (cours 11) pour atteindre 60fps stable

---

## Projet Final

**Audit de performance** d'un projet existant (cours 05 ou 11) :
- Rapport de profiling CPU (flamegraph, cache misses, IPC)
- Rapport de profiling GPU (frame timeline, occupancy, bandwidth)
- Liste priorisée d'optimisations avec gain estimé
- Implémentation des 5 optimisations les plus impactantes
- Mesure avant/après pour chaque optimisation
- Documentation de la méthodologie

**Critère :** Amélioration mesurée d'au moins 2× sur le cas le plus lent.
