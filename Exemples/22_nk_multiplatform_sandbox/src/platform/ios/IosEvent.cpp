#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class IosEvent final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "IosEvent"; }
};

std::unique_ptr<IEventBackend> CreateIosEventBackend() {
    return std::make_unique<IosEvent>();
}

} // namespace nk::detail
