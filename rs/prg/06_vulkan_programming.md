# Cours 06 — Vulkan Programming
**Prérequis :** Cours 01, 03, 04, 05  
**Durée estimée :** 14 semaines  
**Objectif :** Maîtriser Vulkan 1.3 dans son intégralité, comprendre le modèle de synchronisation explicite, et construire un renderer moderne multi-threaded.

---

## Unité 1 — Instance, Device et Swapchain (2 semaines)

### Semaine 1
- Philosophie Vulkan : zéro overhead, tout explicite, multithreading natif
- `VkInstance` : création, layers de validation, extensions
- `VkPhysicalDevice` : énumération, properties, features, queue families
- `VkDevice` logique : création, queues (`VkQueue` graphics, compute, transfer)
- Layers de validation Khronos : `VK_LAYER_KHRONOS_validation`, debug messenger
- **TP :** Bootstrap Vulkan complet : instance → physical device → logical device, avec validation

### Semaine 2
- `VkSurfaceKHR` : création depuis NkWindow (Win32 `VkWin32SurfaceCreateInfoKHR`)
- Swapchain (`VkSwapchainKHR`) : formats, present modes (FIFO, MAILBOX, IMMEDIATE)
- `VkImageView` pour les images de la swapchain
- `VkRenderPass` : attachments, subpasses, subpass dependencies
- `VkFramebuffer` : liaison renderpass + image views
- **TP :** Triangle NDC avec swapchain fonctionnelle, render pass et framebuffers

---

## Unité 2 — Pipeline Graphics et Command Buffers (2 semaines)

### Semaine 3
- `VkShaderModule` : chargement de SPIR-V
- `VkPipelineLayout` : push constants, descriptor set layouts
- `VkGraphicsPipeline` : vertex input, input assembly, viewport, rasterizer, multisample, depth/stencil, color blend, dynamic states
- Dynamic rendering (Vulkan 1.3) : `VK_KHR_dynamic_rendering`, sans renderpass explicite
- Pipeline cache : `VkPipelineCache`, sérialisation sur disque
- **TP :** Pipeline graphics complet avec vertex buffer, index buffer, uniforms

### Semaine 4
- `VkCommandPool` et `VkCommandBuffer` : allocation, recording, submission
- Cycle de vie d'une frame : `vkAcquireNextImageKHR` → record → `vkQueueSubmit` → `vkQueuePresentKHR`
- Fences (`VkFence`) : synchronisation CPU/GPU
- Semaphores (`VkSemaphore`) : synchronisation GPU/GPU (image available, render finished)
- Frames in flight : multiple command buffers, synchronisation correcte
- **TP :** Rendu fluide avec 2 frames in flight, cubes rotatifs

---

## Unité 3 — Mémoire et Ressources (2 semaines)

### Semaine 5
- Memory types Vulkan : `VK_MEMORY_PROPERTY_DEVICE_LOCAL`, `HOST_VISIBLE`, `HOST_COHERENT`, `HOST_CACHED`
- Allocation manuelle : `vkAllocateMemory`, `vkBindBufferMemory`, `vkBindImageMemory`
- VMA (Vulkan Memory Allocator) : utilisation recommandée, `VmaAllocation`
- Staging buffers : upload CPU → GPU, transfer queue
- Buffer views, image views, formats de textures
- **TP :** Mesh 3D avec textures, upload via staging buffer, VMA

### Semaine 6
- `VkImage` : layouts (`UNDEFINED`, `TRANSFER_DST_OPTIMAL`, `SHADER_READ_ONLY_OPTIMAL`, `COLOR_ATTACHMENT_OPTIMAL`, `DEPTH_STENCIL_ATTACHMENT_OPTIMAL`)
- Image layout transitions : pipeline barriers
- Mipmapping en Vulkan : génération par blit
- Samplers : `VkSampler`, comparaison avec OpenGL
- Push constants : usage, limites (128 bytes minimum garantis)
- **TP :** Texture avec mipmaps générés sur GPU, push constants pour les transforms

---

## Unité 4 — Descriptors (2 semaines)

### Semaine 7
- Descriptor layout : `VkDescriptorSetLayout`, bindings
- Descriptor pool : `VkDescriptorPool`, allocation
- Descriptor sets : `VkDescriptorSet`, update avec `vkUpdateDescriptorSets`
- Descriptor indexing (Vulkan 1.2) : bindless textures, `UPDATE_AFTER_BIND`
- Push descriptors `VK_KHR_push_descriptor`
- **TP :** Système de matériaux avec descriptor sets, 20 matériaux différents

### Semaine 8
- Descriptor set strategies : 1 per frame, 1 per pass, 1 per material, 1 per object
- Uniform buffers alignés (minUniformBufferOffsetAlignment)
- Dynamic uniform buffers : un seul buffer pour N objets
- Storage buffers pour GPU instancing
- **TP :** 10 000 objets instanciés avec un seul draw call, transforms dans SSBO

---

## Unité 5 — Synchronisation et Multi-threading (2 semaines)

### Semaine 9
- Modèle de synchronisation Vulkan : pipeline stages, access types
- Memory barriers : `VkMemoryBarrier`, `VkBufferMemoryBarrier`, `VkImageMemoryBarrier`
- Pipeline barriers : `vkCmdPipelineBarrier`
- Synchronization2 (Vulkan 1.3) : `vkCmdPipelineBarrier2`, stages et accès simplifiés
- Events Vulkan : `VkEvent`, set/wait entre command buffers
- **TP :** Pipeline de rendu avec passes séquentielles correctement synchronisées

### Semaine 10
- Multi-threading en Vulkan : command pools par thread, secondary command buffers
- `vkCmdExecuteCommands` : assemblage de secondary buffers
- Job system pour le recording parallèle
- Transfer queue asynchrone : streaming de ressources en arrière-plan
- Compute queue asynchrone : simulation GPU pendant le rendu
- **TP :** Frame recording multi-threadé sur 4 threads, mesure du speedup

---

## Unité 6 — Techniques de rendu avancées en Vulkan (2 semaines)

### Semaine 11
- Shadow mapping Vulkan : render pass dédié, depth attachment
- Subpasses pour deferred shading (input attachments)
- Transient attachments : économie de bande passante mémoire
- Tile-based rendering (mobile) : `LAZILY_ALLOCATED` memory
- **TP :** Deferred shading avec subpasses Vulkan, mesure de bande passante

### Semaine 12
- Mesh shaders Vulkan : `VK_EXT_mesh_shader`, task + mesh stages
- Ray tracing Vulkan : `VK_KHR_ray_tracing_pipeline`, BLAS/TLAS, SBT (Shader Binding Table)
- Ray generation, closest hit, miss, any hit shaders
- Hybrid rendering : ray tracing pour les ombres, rasterisation pour le reste
- **TP :** Ombres ray-traced en Vulkan hybride

---

## Unité 7 — Robustesse et outils (2 semaines)

### Semaine 13
- Gestion des erreurs Vulkan : `VkResult`, crash debugs
- RenderDoc pour Vulkan : frame capture, analyse de ressources, synchronisation timeline
- Validation layers avancées : best practices, GPU-assisted validation
- Profiling : Vulkan timestamp queries, outils vendor (NSight, Radeon GPU Profiler)
- Swapchain recreation : resize de fenêtre, `VK_ERROR_OUT_OF_DATE_KHR`
- **TP :** Debug complet d'une frame avec RenderDoc, rapport de performance

### Semaine 14
- Vulkan portability (MoltenVK pour macOS) : différences de comportement
- Vulkan SC (Safety Critical) : introduction
- Pipeline de build de shaders offline : dxc/glslang → SPIR-V → reflection
- Abstraction layer : comment concevoir un renderer abstrait par-dessus Vulkan
- Migration OpenGL → Vulkan : stratégies
- **TP :** Portage du renderer OpenGL du cours 05 vers Vulkan

---

## Projet Final

**Renderer Vulkan de production** :
- Pipeline deferred avec subpasses
- PBR + IBL
- Shadow mapping
- Ray-traced ambient occlusion (VK_KHR_ray_tracing_pipeline)
- Multi-threaded frame recording
- Streaming de textures asynchrone (transfer queue)
- GPU-driven rendering (indirect draw + GPU culling)
- Documentation de la synchronisation (schéma timeline)

**Cible :** 60fps en 1440p, frame time GPU < 12ms, zéro validation error.
