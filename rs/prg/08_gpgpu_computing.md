# Cours 08 — GPGPU & GPU Computing (CUDA + Compute Shaders)
**Prérequis :** Cours 01, 04, C++ avancé  
**Durée estimée :** 10 semaines  
**Objectif :** Exploiter pleinement la puissance de calcul du GPU pour des tâches non-graphiques et des simulations massivement parallèles.

---

## Unité 1 — Architecture GPU et modèle CUDA (2 semaines)

### Semaine 1
- Architecture GPU NVIDIA : SM (Streaming Multiprocessor), CUDA cores, tensor cores
- Hiérarchie mémoire : registres, L1/L2 cache, shared memory, global memory, constant memory, texture memory
- Modèle d'exécution CUDA : grilles, blocs, threads — `gridDim`, `blockDim`, `threadIdx`, `blockIdx`
- Warp : 32 threads, SIMT, warp divergence
- Setup CUDA : nvcc, `__global__`, `__device__`, `__host__`
- Premier kernel : addition de vecteurs, `cudaMalloc`, `cudaMemcpy`, `cudaFree`
- **TP :** Benchmark CPU vs GPU pour addition de vecteurs (1M, 10M, 100M éléments)

### Semaine 2
- Gestion de la mémoire CUDA :
  - Global memory : latence, coalescing (accès contigus alignés)
  - Shared memory : `__shared__`, taille configurable, bank conflicts
  - Constant memory : broadcast, cache L1
  - Pinned memory : `cudaMallocHost`, transfers DMA sans copie
  - Unified Memory : `cudaMallocManaged`, migration automatique
- Profiling CUDA : `nvprof`, Nsight Systems, Nsight Compute
- **TP :** Multiplication de matrices naïve vs optimisée avec shared memory (tiling), mesure du speedup

---

## Unité 2 — Algorithmes GPU fondamentaux (2 semaines)

### Semaine 3
- Réduction parallèle : sum, min, max — algorithme en log(N) étapes
- Optimisations de réduction : éviter la divergence de warps, unrolling
- Warp-level primitives : `__shfl_down_sync`, `__ballot_sync`, `__reduce_add_sync`
- Scan (prefix sum) : algorithme de Hillis-Steele, algorithme de Blelloch (work-efficient)
- Applications : stream compaction, histogram exclusif
- **TP :** Réduction et scan from scratch, comparaison avec cuBLAS/Thrust

### Semaine 4
- Radix sort GPU : stabilité, passes de comptage, scatter
- Histogram : atomic operations, privatization par bloc
- Stream compaction : filtrage parallèle d'un tableau
- Sparse matrix-vector multiplication (SpMV)
- Convolution 2D GPU : séparable, tiling avec halo
- **TP :** Pipeline de traitement d'image GPU : chargement → convolution → histogram → sort

---

## Unité 3 — Simulation physique GPU (2 semaines)

### Semaine 5
- Simulation de fluides : méthode SPH (Smoothed Particle Hydrodynamics) sur GPU
- Spatial hashing : grille uniforme pour les paires de particules proches
- Intégration numérique : Euler, Verlet, Runge-Kutta sur GPU
- N-body simulation : forces gravitationnelles O(N²) optimisées
- **TP :** Simulation SPH de 100 000 particules à temps réel

### Semaine 6
- Simulation de tissu (cloth simulation) : contraintes de distance, position-based dynamics
- Collision détection GPU : broad phase (SAP, grid), narrow phase
- Rigid body dynamics basique sur GPU
- Simulation de fumée : grille eulérienne 3D, advection, projection
- **TP :** Simulation de tissu 3D interactif en temps réel

---

## Unité 4 — Traitement d'images et vision GPU (2 semaines)

### Semaine 7
- CUDA Texture objects : interpolation hardware, coordonnées normalisées
- Traitement d'image GPU : filtres de convolution (Gaussian, Sobel, Laplacian)
- Transformée de Fourier rapide (FFT) : cuFFT, convolution dans le domaine fréquentiel
- Algorithme de Canny (détection de contours) from scratch sur GPU
- Décompression JPEG basique sur GPU
- **TP :** Pipeline de traitement d'image temps réel : flux webcam → filtres GPU → affichage

### Semaine 8
- BVH (Bounding Volume Hierarchy) construction GPU
- Raytracing GPU from scratch avec CUDA
- Denoising basique : spatial, temporal
- Optical flow GPU (Lucas-Kanade)
- Interop CUDA/OpenGL : `cudaGraphicsGLRegisterBuffer`, rendu sans copie CPU
- **TP :** Raytracer CUDA : sphères, triangles, ombres, 1080p en temps réel

---

## Unité 5 — Compute Shaders cross-platform (2 semaines)

### Semaine 9
- Compute shaders vs CUDA : différences, use cases
- Compute en OpenGL (cours 05 référence), Vulkan et DX12
- Synchronisation compute/graphics : memory barriers, semaphores
- Persistent threads et work stealing GPU
- GPU-driven animation : skinning en compute
- **TP :** Skinning de personnage en compute shader, 100 personnages à 60fps

### Semaine 10
- WebGPU compute : introduction pour portabilité future
- OpenCL : interopérabilité avec d'autres vendors GPU
- CPU fallback gracieux quand GPU indisponible
- CUDA Graphs : capture et replay de séquences de kernels
- Multi-GPU : NVLink, peer access, `cudaMemcpyPeer`
- **TP :** Pipeline de rendu avec CUDA Graphs, mesure de réduction d'overhead

---

## Projet Final

**Moteur de simulation GPU** :
- Simulation SPH fluides + cloth simulation
- Rendu avec raytracing CUDA + interop OpenGL
- Post-processing compute shader
- 60fps pour 500 000 particules
- Profiling Nsight complet, analyse des bottlenecks mémoire et compute
