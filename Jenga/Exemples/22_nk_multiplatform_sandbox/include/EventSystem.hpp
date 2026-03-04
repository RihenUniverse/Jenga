#pragma once

#include <deque>
#include <functional>
#include <memory>
#include <unordered_map>
#include <vector>

#include "Event.hpp"

namespace nk {
namespace detail {
class IEventBackend;
}

struct EventTypeHash {
    std::size_t operator()(EventType value) const {
        return static_cast<std::size_t>(value);
    }
};

class EventSystem {
public:
    using AnyCallback = std::function<void(Event*)>;

    static EventSystem& instance();

    void setGlobalEventCallback(AnyCallback callback);

    template <typename TEvent>
    void setEventCallback(std::function<void(TEvent*)> callback) {
        callbacks_[TEvent::StaticType()].push_back(
            [callback = std::move(callback)](Event* event) {
                callback(static_cast<TEvent*>(event));
            }
        );
    }

    void pushEvent(std::unique_ptr<Event> event);
    std::unique_ptr<Event> pollEvent();

    void clearCallbacks();

private:
    EventSystem();

    void dispatch(Event* event);
    void drainBackendEvents();

    std::deque<std::unique_ptr<Event>> queue_;
    std::unordered_map<EventType, std::vector<AnyCallback>, EventTypeHash> callbacks_;
    AnyCallback globalCallback_;
    std::unique_ptr<detail::IEventBackend> backend_;
};

} // namespace nk
