#include "GraphicsContext.hpp"

#include "Platform.hpp"

namespace nk {

const char* getAPIName(RendererAPI api) {
    switch (api) {
    case RendererAPI::Auto: return "Auto";
    case RendererAPI::OpenGL: return "OpenGL";
    case RendererAPI::Vulkan: return "Vulkan";
    case RendererAPI::Metal: return "Metal";
    case RendererAPI::DirectX12: return "DirectX12";
    default: return "Unknown";
    }
}

GraphicsContext& GraphicsContext::instance() {
    static GraphicsContext instance;
    return instance;
}

bool GraphicsContext::initialize(RendererAPI api) {
    if (initialized_) {
        return true;
    }

    api_ = (api == RendererAPI::Auto) ? RendererAPI::OpenGL : api;

    if (detectPlatform() == PlatformBackend::Macos || detectPlatform() == PlatformBackend::Ios) {
        if (api_ == RendererAPI::OpenGL) {
            api_ = RendererAPI::Metal;
        }
    }

    if (detectPlatform() == PlatformBackend::Win32 && api_ == RendererAPI::Auto) {
        api_ = RendererAPI::DirectX12;
    }

    gpuInfo_.vendor = "NK Virtual GPU";
    gpuInfo_.renderer = "NK Software Stub";
    gpuInfo_.version = "1.0";
    gpuInfo_.shadingLanguageVersion = "1.0";
    gpuInfo_.maxTextureSize = 16384;
    gpuInfo_.supportsCompute = true;
    gpuInfo_.extensions = {"NK_stub_extension"};

    initialized_ = true;
    return true;
}

void GraphicsContext::shutdown() {
    initialized_ = false;
    api_ = RendererAPI::Auto;
}

bool GraphicsContext::isInitialized() const {
    return initialized_;
}

std::vector<RendererAPI> GraphicsContext::getSupportedAPIs() const {
    const PlatformBackend platform = detectPlatform();

    switch (platform) {
    case PlatformBackend::Win32:
        return {RendererAPI::DirectX12, RendererAPI::Vulkan, RendererAPI::OpenGL};
    case PlatformBackend::Macos:
    case PlatformBackend::Ios:
        return {RendererAPI::Metal, RendererAPI::Vulkan, RendererAPI::OpenGL};
    case PlatformBackend::Emscripten:
        return {RendererAPI::OpenGL};
    default:
        return {RendererAPI::OpenGL, RendererAPI::Vulkan};
    }
}

RendererAPI GraphicsContext::getAPI() const {
    return api_;
}

const GPUInfo& GraphicsContext::getGPUInfo() const {
    return gpuInfo_;
}

void GraphicsContext::setDebugMode(bool value) {
    debugMode_ = value;
}

bool GraphicsContext::isDebugMode() const {
    return debugMode_;
}

} // namespace nk
