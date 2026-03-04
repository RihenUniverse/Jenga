# Cours 04 — Shaders & Langages GPU (GLSL / HLSL / SPIR-V)
**Prérequis :** Cours 01, 03  
**Durée estimée :** 6 semaines  
**Objectif :** Maîtriser l'écriture de shaders dans les trois grands langages GPU, comprendre la compilation vers SPIR-V, et produire des effets visuels avancés.

---

## Unité 1 — Architecture GPU et modèle d'exécution (1 semaine)

### Semaine 1
- Architecture GPU : streaming multiprocessors, warps/wavefronts, SIMT
- Différence CPU threading vs GPU threading
- Pipeline de compilation de shader : source → AST → IR → bytecode GPU
- Stages du pipeline graphique : vertex, tessellation, geometry, fragment, compute
- Invocations parallèles : built-ins `gl_VertexID`, `gl_FragCoord`, `SV_Position`
- **TP :** Compiler et exécuter un premier shader GLSL avec un triangle NDC hardcodé

---

## Unité 2 — GLSL (OpenGL Shading Language) (2 semaines)

### Semaine 2
- Syntaxe GLSL : types scalaires, vecteurs, matrices, tableaux, structs
- Qualifiers : `in`, `out`, `uniform`, `layout(location=...)`, `layout(binding=...)`
- Fonctions built-in : `dot`, `cross`, `normalize`, `reflect`, `refract`, `mix`, `clamp`, `step`, `smoothstep`
- Vertex shader complet : MVP transform, passage d'attributs
- Fragment shader complet : Blinn-Phong, texture lookup `texture(sampler2D, uv)`
- Précision : `highp`, `mediump`, `lowp` (mobile)
- **TP :** Shader Blinn-Phong avec normale en espace monde, 3 lumières ponctuelles

### Semaine 3
- Geometry shader : émission de primitives, `EmitVertex`, `EndPrimitive`
- Usage : génération de normales visuelles, grass instancing, shadow volumes
- Tessellation shader : hull shader + domain shader, `gl_TessLevelOuter/Inner`
- Displacement mapping avec tessellation
- Compute shader GLSL : `layout(local_size_x=...)`, `gl_GlobalInvocationID`, barrières
- Shared memory, atomics
- **TP :** Terrain avec tessellation adaptive + displacement, Compute shader tri de particules

---

## Unité 3 — HLSL (High-Level Shader Language) (2 semaines)

### Semaine 4
- Syntaxe HLSL vs GLSL : différences et similitudes
- Types : `float4`, `float4x4`, `SamplerState`, `Texture2D`, `cbuffer`
- Semantics : `POSITION`, `TEXCOORD`, `SV_Position`, `SV_Target`, `SV_Depth`
- Vertex shader et pixel shader HLSL
- Constant buffers (cbuffer) : alignement 16 bytes, packing
- Structured buffers : `StructuredBuffer<T>`, `RWStructuredBuffer<T>`
- **TP :** Réécrire le shader Blinn-Phong du cours OpenGL en HLSL pour DirectX

### Semaine 5
- HLSL Compute shader : `[numthreads(x,y,z)]`, `SV_DispatchThreadID`, `GroupMemoryBarrierWithGroupSync`
- UAV (Unordered Access Views) : lecture/écriture arbitraire
- Wave intrinsics HLSL (Shader Model 6.0) : `WaveActiveSum`, `WavePrefixSum`
- Hull shader et domain shader HLSL
- Ray tracing shaders (Shader Model 6.5) : introduction `[shader("raygeneration")]`
- **TP :** Compute shader HLSL : reduction parallèle, prefix sum

---

## Unité 4 — SPIR-V et compilation de shaders (1 semaine)

### Semaine 6
- Qu'est-ce que SPIR-V : format binaire intermédiaire, structure modulaire
- Chaîne de compilation : GLSL → SPIR-V (glslang/shaderc), HLSL → SPIR-V (dxc)
- Lire et comprendre du bytecode SPIR-V : `spirv-dis`, modules, décorateurs
- Cross-compilation avec SPIRV-Cross : SPIR-V → GLSL/HLSL/MSL/WGSL
- Reflection de shaders : extraire les bindings, les types, les uniform layouts
- Compilation à runtime vs offline compilation
- **TP :** Pipeline de build automatique : GLSL + HLSL → SPIR-V, reflection automatique des bindings

---

## Projet Final

**Librairie de shaders** réutilisable comprenant :
- Shaders GLSL et HLSL équivalents pour : Blinn-Phong, PBR (GGX), normal mapping, shadow mapping, tone mapping ACES
- Compute shaders : prefix sum, histogram, blur séparable
- Pipeline de compilation offline vers SPIR-V avec reflection
- Documentation des uniforms et bindings pour chaque shader

**Évaluation :** Exactitude visuelle (comparaison screenshots), qualité SPIR-V généré, documentation.
