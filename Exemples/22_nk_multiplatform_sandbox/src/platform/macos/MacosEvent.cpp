#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class MacosEvent final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "MacosEvent"; }
};

std::unique_ptr<IEventBackend> CreateMacosEventBackend() {
    return std::make_unique<MacosEvent>();
}

} // namespace nk::detail
