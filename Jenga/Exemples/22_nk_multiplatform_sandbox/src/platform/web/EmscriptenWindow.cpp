#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class EmscriptenWindow final : public IWindowBackend {
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
    const char* Name() const override { return "EmscriptenWindow"; }

private:
    bool open_ = false;
    int width_ = 0;
    int height_ = 0;
};

std::unique_ptr<IWindowBackend> CreateEmscriptenWindowBackend() {
    return std::make_unique<EmscriptenWindow>();
}

} // namespace nk::detail
