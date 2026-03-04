#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class XlibWindow final : public IWindowBackend {
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
    const char* Name() const override { return "XlibWindow"; }

private:
    bool open_ = false;
    int width_ = 0;
    int height_ = 0;
};

std::unique_ptr<IWindowBackend> CreateXlibWindowBackend() {
    return std::make_unique<XlibWindow>();
}

} // namespace nk::detail
