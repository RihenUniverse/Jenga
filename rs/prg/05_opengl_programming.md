# Cours 05 — OpenGL Programming
**Prérequis :** Cours 01, 03, 04  
**Durée estimée :** 10 semaines  
**Objectif :** Maîtriser OpenGL 4.6 Core Profile, comprendre le driver model, et construire un renderer 3D complet avec les techniques modernes.

---

## Unité 1 — OpenGL moderne : setup et objets GPU (2 semaines)

### Semaine 1
- OpenGL Core Profile vs Compatibility Profile
- Création de contexte OpenGL avec NkWindow (ou WGL/GLX)
- Chargement des extensions : GLAD
- State machine OpenGL : bind model, contexte courant
- VAO (Vertex Array Object), VBO (Vertex Buffer Object), EBO (Element Buffer Object)
- `glBufferData` vs `glBufferSubData` vs `glNamedBufferStorage` (DSA)
- **TP :** Afficher un triangle, puis un cube texturé avec VBO/VAO/EBO

### Semaine 2
- DSA (Direct State Access) : `glCreateBuffers`, `glNamedBufferStorage`, `glVertexArrayAttribBinding`
- Texture objects : `glCreateTextures`, formats (GL_RGBA8, GL_RGB16F, GL_DEPTH24_STENCIL8)
- Texture filtering, wrapping, mipmaps
- Samplers objects : `glCreateSamplers`, binding séparé du sampler et de la texture
- UBO (Uniform Buffer Objects) : binding points, alignement std140/std430
- SSBO (Shader Storage Buffer Objects) : accès compute et graphique
- **TP :** Scène multi-objets avec UBO pour la caméra et les lumières (binding 0/1)

---

## Unité 2 — Framebuffers et rendu off-screen (2 semaines)

### Semaine 3
- FBO (Framebuffer Objects) : création, attachements (color, depth, stencil)
- Render to texture : FBO + texture attachment
- Multisample FBO (MSAA) : `GL_TEXTURE_2D_MULTISAMPLE`, `glBlitFramebuffer`
- Floating-point framebuffers (HDR) : `GL_RGBA16F`, `GL_RGBA32F`
- **TP :** Pipeline de rendu en deux passes : rendu HDR → post-process tone mapping

### Semaine 4
- Stencil buffer : masquage, stencil shadow volumes
- Depth peeling pour la transparence OIT
- Layered rendering : `GL_TEXTURE_2D_ARRAY`, geometry shader pour shadow cube map
- `glDrawBuffers` : Multiple Render Targets (MRT) — G-Buffer pour deferred shading
- **TP :** G-Buffer complet : position, normale, albedo dans 3 textures, reconstruction en post-process

---

## Unité 3 — Techniques de rendu avancées (3 semaines)

### Semaine 5
- Shadow mapping : depth FBO, comparaison de profondeur, `sampler2DShadow`
- Cascaded Shadow Maps (CSM) : partitionnement du frustum, sélection de cascade
- Point light shadows : cube shadow map, face selection en géometry shader
- **TP :** CSM avec 4 cascades, debug visualization des cascades

### Semaine 6
- Deferred shading : G-Buffer pass + lighting pass
- Tiled deferred shading concept (frustum culling de lumières par tile)
- SSAO (Screen Space Ambient Occlusion) : hemisphere sampling, blur
- Screen Space Reflections (SSR) : ray marching sur le depth buffer
- **TP :** Pipeline deferred complet : 50+ lumières ponctuelles, SSAO

### Semaine 7
- PBR (Physically Based Rendering) : metallic-roughness workflow
- BRDF de Cook-Torrance : distribution GGX, Fresnel Schlick, geometry Smith
- IBL (Image Based Lighting) : préfiltrage de l'environnement, split-sum approximation
- Génération offline des cubemaps IBL avec compute shaders
- **TP :** Matériaux PBR avec IBL, comparaison avec référence (Blender Cycles)

---

## Unité 4 — Compute et GPU-driven rendering (2 semaines)

### Semaine 8
- Compute shaders OpenGL : `glDispatchCompute`, `glMemoryBarrier`
- Particle system sur GPU : update et rendu 100% GPU
- GPU culling : frustum + occlusion culling en compute shader
- `glDrawArraysIndirect` / `glMultiDrawElementsIndirect` : draw calls indirects
- **TP :** Particle system GPU : 1 million de particules à 60fps

### Semaine 9
- Texture streaming : `glTextureStorage`, `glCompressedTextureSubImage`
- Formats compressés : DXT/BC1-7, ASTC
- Sparse textures (virtual texturing concept)
- Debug OpenGL : `GL_DEBUG_OUTPUT`, `glPushDebugGroup`, RenderDoc integration
- Timer queries : `GL_TIME_ELAPSED`, profiling GPU précis
- **TP :** Profiling complet d'une frame, identifier et corriger les bottlenecks GPU

---

## Unité 5 — OpenGL avancé et extensions (1 semaine)

### Semaine 10
- Bindless textures : `glGetTextureHandleARB`, passage dans SSBO
- Mesh shaders (NV_mesh_shader / ARB_mesh_shader)
- Ray queries (GL_NV_ray_tracing ou fallback software)
- OpenGL sur mobile : OpenGL ES 3.2, différences avec desktop
- Interop OpenGL/CUDA pour le traitement d'image GPU
- **TP :** Renderer bindless : 10 000 objets avec textures différentes, 0 texture bind

---

## Projet Final

**Renderer 3D OpenGL complet** affichant la scène Sponza avec :
- Pipeline deferred shading
- PBR + IBL
- CSM (4 cascades)
- SSAO
- Post-processing : bloom, ACES tone mapping, FXAA
- GPU-driven culling
- Profiling RenderDoc documenté

**Cible performance :** 60fps en 1080p sur GPU mid-range, GPU frame time documenté.
