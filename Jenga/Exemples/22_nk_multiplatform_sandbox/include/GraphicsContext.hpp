#pragma once

#include <string>
#include <vector>

namespace nk {

enum class RendererAPI {
    Auto = 0,
    OpenGL,
    Vulkan,
    Metal,
    DirectX12
};

const char* getAPIName(RendererAPI api);

struct GPUInfo {
    std::string vendor = "UnknownVendor";
    std::string renderer = "UnknownRenderer";
    std::string version = "0.0";
    std::string shadingLanguageVersion = "0.0";
    int maxTextureSize = 0;
    bool supportsCompute = false;
    std::vector<std::string> extensions;
};

class GraphicsContext {
public:
    static GraphicsContext& instance();

    bool initialize(RendererAPI api);
    void shutdown();

    bool isInitialized() const;

    std::vector<RendererAPI> getSupportedAPIs() const;
    RendererAPI getAPI() const;

    const GPUInfo& getGPUInfo() const;

    void setDebugMode(bool value);
    bool isDebugMode() const;

private:
    GraphicsContext() = default;

    RendererAPI api_ = RendererAPI::Auto;
    GPUInfo gpuInfo_;
    bool initialized_ = false;
    bool debugMode_ = false;
};

} // namespace nk
