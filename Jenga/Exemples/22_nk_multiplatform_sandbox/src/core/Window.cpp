#include "Window.hpp"

#include <utility>

#include "EventSystem.hpp"
#include "../internal/NativeBackends.hpp"

namespace nk {

Window::Window(const WindowConfig& config)
    : config_(config),
      platform_(detectPlatform()),
      backend_(detail::CreateWindowBackend(platform_)) {
    if (backend_) {
        valid_ = backend_->Create(config_);
    }

    if (valid_) {
        EventSystem::instance().pushEvent(std::make_unique<WindowResizeEvent>(this, getWidth(), getHeight()));
    }
}

Window::~Window() {
    if (isOpen()) {
        close();
    }
}

Window::Window(Window&& other) noexcept = default;
Window& Window::operator=(Window&& other) noexcept = default;

bool Window::isValid() const {
    return valid_;
}

bool Window::isOpen() const {
    return backend_ && backend_->IsOpen();
}

void Window::pollEvents() {
    if (backend_) {
        backend_->PollEvents();
    }
}

void Window::close() {
    if (!backend_ || !backend_->IsOpen()) {
        return;
    }

    backend_->Close();
    EventSystem::instance().pushEvent(std::make_unique<WindowCloseEvent>(this));
}

int Window::getWidth() const {
    return backend_ ? backend_->Width() : config_.width;
}

int Window::getHeight() const {
    return backend_ ? backend_->Height() : config_.height;
}

const WindowConfig& Window::getConfig() const {
    return config_;
}

PlatformBackend Window::getPlatform() const {
    return platform_;
}

std::string Window::getBackendName() const {
    return backend_ ? backend_->Name() : "Unavailable";
}

} // namespace nk
