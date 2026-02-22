#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class XlibEvent final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "XlibEvent"; }
};

std::unique_ptr<IEventBackend> CreateXlibEventBackend() {
    return std::make_unique<XlibEvent>();
}

} // namespace nk::detail
