#include "../../internal/NativeBackends.hpp"

namespace nk::detail {

class Win32Event final : public IEventBackend {
public:
    std::vector<std::unique_ptr<Event>> Pump() override {
        return {};
    }

    const char* Name() const override { return "Win32Event"; }
};

std::unique_ptr<IEventBackend> CreateWin32EventBackend() {
    return std::make_unique<Win32Event>();
}

} // namespace nk::detail
