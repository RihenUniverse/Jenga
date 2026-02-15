#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class HarmonyEvent final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "HarmonyEvent"; }
};

std::unique_ptr<IEventBackend> CreateHarmonyEventBackend() {
    return std::make_unique<HarmonyEvent>();
}

} // namespace nk::detail
