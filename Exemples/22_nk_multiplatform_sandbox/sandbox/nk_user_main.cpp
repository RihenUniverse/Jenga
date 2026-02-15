#include <chrono>
#include <cmath>
#include <iostream>

#include "nk.hpp"

namespace nk {

int nk_main(int argc, char** argv) {
    (void)argc;
    (void)argv;

    std::cou << "=== NK Framework Initialization ===" << std::endl;

    auto& graphicsContext = GraphicsContext::instance();

    std::cout << "\nAvailable Graphics APIs:" << std::endl;
    const auto apis = graphicsContext.getSupportedAPIs();
    for (RendererAPI api : apis) {
        std::cout << "  - " << getAPIName(api) << std::endl;
    }

    if (!graphicsContext.initialize(RendererAPI::OpenGL)) {
        std::cerr << "Failed to initialize graphics context" << std::endl;
        return -1;
    }

    const GPUInfo& gpuInfo = graphicsContext.getGPUInfo();
    std::cout << "\nGPU Information:" << std::endl;
    std::cout << "  Vendor: " << gpuInfo.vendor << std::endl;
    std::cout << "  Renderer: " << gpuInfo.renderer << std::endl;
    std::cout << "  Version: " << gpuInfo.version << std::endl;

    auto& eventSystem = EventSystem::instance();
    eventSystem.setGlobalEventCallback([](Event* event) {
        (void)event;
    });

    WindowConfig config;
    config.title = "NK Sandbox";
    config.width = 1280;
    config.height = 720;

    Window window(config);
    if (!window.isValid()) {
        std::cerr << "Failed to create sandbox window" << std::endl;
        return -1;
    }

    RendererConfig rendererConfig;
    rendererConfig.api = graphicsContext.getAPI();
    rendererConfig.vsync = true;
    rendererConfig.multisampling = 4;

    Renderer renderer(window, rendererConfig);
    if (!renderer.isValid()) {
        std::cerr << "Failed to create renderer" << std::endl;
        return -1;
    }

    bool running = true;
    int frameCount = 0;

    eventSystem.setEventCallback<WindowCloseEvent>([&](WindowCloseEvent*) {
        running = false;
    });

    eventSystem.setEventCallback<KeyPressedEvent>([&](KeyPressedEvent* event) {
        if (event->getKey() == Key::Escape) {
            running = false;
        }
    });

    const auto begin = std::chrono::high_resolution_clock::now();
    std::cout << "\n=== Starting Main Loop ===" << std::endl;

    while (running && window.isOpen()) {
        while (auto event = eventSystem.pollEvent()) {
            (void)event;
        }

        window.pollEvents();

        const float time = static_cast<float>(frameCount) * 0.016f;
        const float r = (std::sin(time) + 1.0f) * 0.5f;
        const float g = (std::cos(time) + 1.0f) * 0.5f;
        const float b = 0.2f;

        renderer.beginFrame();
        renderer.clear(r, g, b, 1.0f);

        const FramebufferInfo fb = renderer.getFramebufferInfo();
        const int cx = fb.width / 2;
        const int cy = fb.height / 2;
        const int radius = 40 + static_cast<int>(std::sin(time * 2.0f) * 20.0f);

        const uint32_t white = renderer.packColor(255, 255, 255, 255);
        renderer.drawCircle(cx, cy, radius, white);
        renderer.drawLine(cx - 120, cy, cx + 120, cy, white);
        renderer.drawLine(cx, cy - 120, cx, cy + 120, white);

        renderer.endFrame();
        renderer.present();

        frameCount++;
        if (frameCount > 300) {
            running = false;
            window.close();
        }
    }

    const auto end = std::chrono::high_resolution_clock::now();
    const float elapsed = std::chrono::duration<float>(end - begin).count();

    std::cout << "Frames: " << frameCount << " in " << elapsed << " seconds" << std::endl;

    graphicsContext.shutdown();
    std::cout << "Shutdown complete" << std::endl;

    return 0;
}

} // namespace nk
