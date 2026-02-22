#include <iostream>

#include "nk.hpp"

int main() {
    auto& context = nk::GraphicsContext::instance();
    if (!context.initialize(nk::RendererAPI::Auto)) {
        std::cerr << "GraphicsContext initialization failed" << std::endl;
        return 1;
    }

    nk::WindowConfig config;
    config.title = "Sandbox Test";
    config.width = 640;
    config.height = 360;

    nk::Window window(config);
    if (!window.isValid()) {
        std::cerr << "Window creation failed" << std::endl;
        return 2;
    }

    nk::Renderer renderer(window, {});
    if (!renderer.isValid()) {
        std::cerr << "Renderer creation failed" << std::endl;
        return 3;
    }

    auto& events = nk::EventSystem::instance();
    window.close();

    bool sawClose = false;
    while (auto event = events.pollEvent()) {
        if (event->getType() == nk::EventType::WindowClose) {
            sawClose = true;
            break;
        }
    }

    context.shutdown();

    if (!sawClose) {
        std::cerr << "WindowClose event not received" << std::endl;
        return 4;
    }

    std::cout << "Sandbox test passed" << std::endl;
    return 0;
}
