#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class EmscriptenEvent final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "EmscriptenEvent"; }
};

std::unique_ptr<IEventBackend> CreateEmscriptenEventBackend() {
    return std::make_unique<EmscriptenEvent>();
}

} // namespace nk::detail
