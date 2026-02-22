#include "Renderer.hpp"

namespace nk {

Renderer::Renderer(Window& window, const RendererConfig& config)
    : window_(&window), config_(config) {
    if (config_.api == RendererAPI::Auto) {
        config_.api = GraphicsContext::instance().getAPI();
    }

    valid_ = window_->isValid() && GraphicsContext::instance().isInitialized();
}

bool Renderer::isValid() const {
    return valid_;
}

const char* Renderer::getAPIName() const {
    return nk::getAPIName(config_.api);
}

void Renderer::beginFrame() {
    (void)window_;
}

void Renderer::clear(float r, float g, float b, float a) {
    (void)r;
    (void)g;
    (void)b;
    (void)a;
}

void Renderer::drawCircle(int centerX, int centerY, int radius, uint32_t color) {
    (void)centerX;
    (void)centerY;
    (void)radius;
    (void)color;
}

void Renderer::drawLine(int x1, int y1, int x2, int y2, uint32_t color) {
    (void)x1;
    (void)y1;
    (void)x2;
    (void)y2;
    (void)color;
}

void Renderer::setPixel(int x, int y, uint32_t color) {
    (void)x;
    (void)y;
    (void)color;
}

void Renderer::endFrame() {
}

void Renderer::present() {
}

FramebufferInfo Renderer::getFramebufferInfo() const {
    if (!window_) {
        return {};
    }

    return {window_->getWidth(), window_->getHeight()};
}

uint32_t Renderer::packColor(uint8_t r, uint8_t g, uint8_t b, uint8_t a) const {
    return static_cast<uint32_t>(r)
        | (static_cast<uint32_t>(g) << 8)
        | (static_cast<uint32_t>(b) << 16)
        | (static_cast<uint32_t>(a) << 24);
}

} // namespace nk
