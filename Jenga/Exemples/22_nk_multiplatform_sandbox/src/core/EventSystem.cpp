#include "EventSystem.hpp"

#include <utility>

#include "../internal/NativeBackends.hpp"
#include "Platform.hpp"

namespace nk {

EventSystem& EventSystem::instance() {
    static EventSystem instance;
    return instance;
}

EventSystem::EventSystem()
    : backend_(detail::CreateEventBackend(detectPlatform())) {}

void EventSystem::setGlobalEventCallback(AnyCallback callback) {
    globalCallback_ = std::move(callback);
}

void EventSystem::pushEvent(std::unique_ptr<Event> event) {
    if (!event) {
        return;
    }
    queue_.push_back(std::move(event));
}

std::unique_ptr<Event> EventSystem::pollEvent() {
    if (queue_.empty()) {
        drainBackendEvents();
    }

    if (queue_.empty()) {
        return nullptr;
    }

    std::unique_ptr<Event> event = std::move(queue_.front());
    queue_.pop_front();

    dispatch(event.get());
    return event;
}

void EventSystem::clearCallbacks() {
    callbacks_.clear();
    globalCallback_ = nullptr;
}

void EventSystem::dispatch(Event* event) {
    if (!event) {
        return;
    }

    if (globalCallback_) {
        globalCallback_(event);
    }

    auto it = callbacks_.find(event->getType());
    if (it == callbacks_.end()) {
        return;
    }

    for (const AnyCallback& callback : it->second) {
        callback(event);
    }
}

void EventSystem::drainBackendEvents() {
    if (!backend_) {
        return;
    }

    std::vector<std::unique_ptr<Event>> produced = backend_->Pump();
    for (std::unique_ptr<Event>& event : produced) {
        if (event) {
            queue_.push_back(std::move(event));
        }
    }
}

} // namespace nk
