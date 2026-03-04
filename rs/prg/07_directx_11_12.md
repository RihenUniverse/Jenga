# Cours 07 — DirectX 11 / 12 Programming
**Prérequis :** Cours 01, 03, 04 (DX11), + Cours 06 fortement recommandé (DX12)  
**Durée estimée :** 12 semaines (5 DX11 + 7 DX12)  
**Objectif :** Maîtriser l'écosystème DirectX sur Windows, DX11 pour la productivité et DX12 pour le contrôle bas niveau.

---

# PARTIE 1 — DirectX 11 (5 semaines)

## Unité 1 — Setup et Device DX11 (1 semaine)

### Semaine 1
- Architecture DirectX 11 : `ID3D11Device`, `ID3D11DeviceContext`, `IDXGISwapChain`
- Création du device : feature levels, debug layer (`D3D11_CREATE_DEVICE_DEBUG`)
- Swapchain DXGI : formats, buffer count, MSAA
- Render Target View (RTV) et Depth Stencil View (DSV)
- Pipeline de rendu d'un triangle HLSL : vertex buffer, input layout, shaders
- **TP :** Triangle DX11 avec swapchain sur NkWindow (HWND)

---

## Unité 2 — Ressources et pipeline DX11 (2 semaines)

### Semaine 2
- Buffers DX11 : vertex, index, constant (`D3D11_BIND_CONSTANT_BUFFER`)
- Usage flags : `DEFAULT`, `DYNAMIC`, `STAGING`, `IMMUTABLE`
- `Map/Unmap` pour les updates CPU
- Textures : `ID3D11Texture2D`, `ID3D11ShaderResourceView`, samplers
- Render states : `ID3D11RasterizerState`, `ID3D11DepthStencilState`, `ID3D11BlendState`
- **TP :** Scène multi-objets avec constant buffers et textures

### Semaine 3
- Pipeline states DX11 : IA, VS, RS, PS, OM — binding au contexte
- Deferred contexts DX11 : command lists pour le multi-threading
- Compute shaders DX11 : `ID3D11ComputeShader`, `ID3D11UnorderedAccessView`
- Structured buffers et typed buffers
- Render to texture, depth of field basique
- **TP :** Deferred shading DX11 complet, compute shader post-processing

---

## Unité 3 — Techniques avancées DX11 (2 semaines)

### Semaine 4
- Shadow mapping DX11
- FXAA en compute shader
- Stream output : capture de primitives pour la simulation GPU
- Hardware instancing : `DrawIndexedInstanced`
- Occlusion queries : `ID3D11Query`

### Semaine 5
- PIX for Windows : frame capture, GPU profiling
- DXGI debug : leak detection
- Interop DX11/CUDA (CUDA surfaces)
- Windows Imaging Component (WIC) : chargement d'images
- **TP :** Profiling frame complet avec PIX, optimisation ciblée

---

# PARTIE 2 — DirectX 12 (7 semaines)

## Unité 4 — Bootstrap DX12 (2 semaines)

### Semaine 6
- Philosophie DX12 vs DX11 : synchronisation explicite, heaps, queues séparées
- `ID3D12Device`, `ID3D12CommandQueue` (direct, compute, copy)
- Descriptor heaps : CBV/SRV/UAV heap, RTV heap, DSV heap, sampler heap
- Swapchain DX12 avec DXGI : `CreateSwapChainForHwnd`
- Command allocators et command lists : `ID3D12GraphicsCommandList`
- Pipeline State Objects (PSO) : `D3D12_GRAPHICS_PIPELINE_STATE_DESC`
- **TP :** Triangle DX12, swap chain, PSO

### Semaine 7
- Root signatures : `ID3D12RootSignature`, root constants, root descriptors, descriptor tables
- Heaps de mémoire GPU : `ID3D12Heap`, `D3D12_HEAP_TYPE_DEFAULT/UPLOAD/READBACK`
- Resource barriers : `D3D12_RESOURCE_STATE_*`, transitions
- Copy queue : upload de ressources, staging buffers
- Fences DX12 : `ID3D12Fence`, signal/wait, frame throttling
- **TP :** Mesh texturé DX12 avec root signature et gestion mémoire explicite

---

## Unité 5 — Techniques avancées DX12 (3 semaines)

### Semaine 8
- Multi-threading DX12 : un command allocator par thread par frame
- Bundle command lists : pré-recording de séquences réutilisables
- Indirect rendering : `ExecuteIndirect`, command signatures
- GPU-driven rendering complet : frustum culling en compute, indirect draw
- **TP :** 10 000 objets GPU-driven avec culling en compute

### Semaine 9
- DirectX Raytracing (DXR) : BLAS, TLAS, `ID3D12StateObject`
- Shader Binding Table (SBT) construction
- Ray generation, closest hit, miss shaders en HLSL
- Inline ray tracing (Shader Model 6.5) : `TraceRayInline`
- **TP :** Ombres et réflexions ray-traced en DXR

### Semaine 10
- DirectML : introduction au machine learning sur DirectX
- Mesh shaders DX12 : amplification + mesh stages
- Variable Rate Shading (VRS) : zones de shading adaptatif
- Sampler feedback : texture streaming et virtual texturing
- **TP :** VRS adaptatif basé sur la vélocité de mouvement

---

## Unité 6 — Outils et production DX12 (2 semaines)

### Semaine 11
- PIX for Windows DX12 : GPU captures, timeline, memory heap analysis
- Debug layer DX12 : `ID3D12Debug3`, GPU-based validation
- DRED (Device Removed Extended Data) : crash post-mortem
- Aftermath (NVIDIA) pour la récupération après GPU crash
- Performance analysis : hardware counters, bandwidth, occupancy

### Semaine 12
- Portage DX11 → DX12 : stratégies de migration
- Interop DX12/Vulkan (via DXGI shared resources)
- Abstraction renderer : couche commune DX11/DX12/Vulkan/OpenGL
- Distribution Windows : WARP software renderer, feature level fallbacks
- **TP :** Renderer abstrait avec backend DX11 et DX12 interchangeable

---

## Projet Final

**Renderer DX12 de production** :
- GPU-driven rendering avec indirect draw
- DirectX Raytracing pour ombres + AO
- Mesh shaders pour le foliage
- Deferred shading + PBR
- Profiling PIX documenté, GPU frame time < 10ms en 1080p
