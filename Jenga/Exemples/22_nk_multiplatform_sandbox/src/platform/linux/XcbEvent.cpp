#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class XcbEvent final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "XcbEvent"; }
};

std::unique_ptr<IEventBackend> CreateXcbEventBackend() {
    return std::make_unique<XcbEvent>();
}

} // namespace nk::detail
