#pragma once

#include <memory>
#include <string>

#include "Platform.hpp"

namespace nk {
namespace detail {
class IWindowBackend;
}

struct WindowConfig {
    std::string title = "NK Window";
    int width = 1280;
    int height = 720;
    int x = 100;
    int y = 100;
    bool visible = true;
};

class Window {
public:
    explicit Window(const WindowConfig& config);
    ~Window();

    Window(Window&& other) noexcept;
    Window& operator=(Window&& other) noexcept;

    Window(const Window&) = delete;
    Window& operator=(const Window&) = delete;

    bool isValid() const;
    bool isOpen() const;

    void pollEvents();
    void close();

    int getWidth() const;
    int getHeight() const;

    const WindowConfig& getConfig() const;
    PlatformBackend getPlatform() const;
    std::string getBackendName() const;

private:
    WindowConfig config_;
    PlatformBackend platform_ = PlatformBackend::Unknown;
    std::unique_ptr<detail::IWindowBackend> backend_;
    bool valid_ = false;
};

} // namespace nk
