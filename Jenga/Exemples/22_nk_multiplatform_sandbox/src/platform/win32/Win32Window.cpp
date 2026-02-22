#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class Win32Window final : public IWindowBackend {
public:
    bool Create(const WindowConfig& config) override {
        width_ = config.width;
        height_ = config.height;
        open_ = true;
        return true;
    }

    void PollEvents() override {}
    bool IsOpen() const override { return open_; }
    void Close() override { open_ = false; }
    int Width() const override { return width_; }
    int Height() const override { return height_; }
    const char* Name() const override { return "Win32Window"; }

private:
    bool open_ = false;
    int width_ = 0;
    int height_ = 0;
};

std::unique_ptr<IWindowBackend> CreateWin32WindowBackend() {
    return std::make_unique<Win32Window>();
}

} // namespace nk::detail
