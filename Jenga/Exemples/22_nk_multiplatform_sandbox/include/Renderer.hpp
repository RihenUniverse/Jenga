#pragma once

#include <cstdint>
#include <string>

#include "GraphicsContext.hpp"
#include "Window.hpp"

namespace nk {

struct RendererConfig {
    RendererAPI api = RendererAPI::Auto;
    bool vsync = true;
    int multisampling = 1;
};

struct FramebufferInfo {
    int width = 0;
    int height = 0;
};

class Renderer {
public:
    Renderer(Window& window, const RendererConfig& config);

    bool isValid() const;
    const char* getAPIName() const;

    void beginFrame();
    void clear(float r, float g, float b, float a);
    void drawCircle(int centerX, int centerY, int radius, uint32_t color);
    void drawLine(int x1, int y1, int x2, int y2, uint32_t color);
    void setPixel(int x, int y, uint32_t color);
    void endFrame();
    void present();

    FramebufferInfo getFramebufferInfo() const;

    uint32_t packColor(uint8_t r, uint8_t g, uint8_t b, uint8_t a) const;

private:
    Window* window_ = nullptr;
    RendererConfig config_;
    bool valid_ = false;
};

} // namespace nk
