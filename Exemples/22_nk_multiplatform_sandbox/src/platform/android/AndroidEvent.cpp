#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class AndroidEvent final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "AndroidEvent"; }
};

std::unique_ptr<IEventBackend> CreateAndroidEventBackend() {
    return std::make_unique<AndroidEvent>();
}

} // namespace nk::detail
