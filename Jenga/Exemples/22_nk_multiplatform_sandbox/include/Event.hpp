#pragma once

#include <cstdint>
#include <string>

namespace nk {

class Window;

enum class EventType : uint32_t {
    None = 0,
    Tick,
    WindowClose,
    WindowResize,
    KeyPressed,
    Custom
};

enum class Key : uint32_t {
    Unknown = 0,
    Escape,
    F1,
    F2
};

class Event {
public:
    virtual ~Event() = default;
    virtual EventType getType() const = 0;
    virtual const char* getName() const = 0;
    virtual std::string toString() const { return getName(); }
};

class TickEvent final : public Event {
public:
    static EventType StaticType() { return EventType::Tick; }

    explicit TickEvent(std::string source) : source_(std::move(source)) {}

    EventType getType() const override { return StaticType(); }
    const char* getName() const override { return "TickEvent"; }
    std::string toString() const override { return std::string(getName()) + "(" + source_ + ")"; }

private:
    std::string source_;
};

class WindowEvent : public Event {
public:
    explicit WindowEvent(Window* window) : window_(window) {}
    Window* getWindow() const { return window_; }

protected:
    Window* window_ = nullptr;
};

class WindowCloseEvent final : public WindowEvent {
public:
    static EventType StaticType() { return EventType::WindowClose; }

    explicit WindowCloseEvent(Window* window) : WindowEvent(window) {}

    EventType getType() const override { return StaticType(); }
    const char* getName() const override { return "WindowCloseEvent"; }
};

class WindowResizeEvent final : public WindowEvent {
public:
    static EventType StaticType() { return EventType::WindowResize; }

    WindowResizeEvent(Window* window, int width, int height)
        : WindowEvent(window), width_(width), height_(height) {}

    EventType getType() const override { return StaticType(); }
    const char* getName() const override { return "WindowResizeEvent"; }

    int getWidth() const { return width_; }
    int getHeight() const { return height_; }

    std::string toString() const override {
        return std::string(getName()) + "(" + std::to_string(width_) + "x" + std::to_string(height_) + ")";
    }

private:
    int width_ = 0;
    int height_ = 0;
};

class KeyPressedEvent final : public WindowEvent {
public:
    static EventType StaticType() { return EventType::KeyPressed; }

    KeyPressedEvent(Window* window, Key key) : WindowEvent(window), key_(key) {}

    EventType getType() const override { return StaticType(); }
    const char* getName() const override { return "KeyPressedEvent"; }

    Key getKey() const { return key_; }

private:
    Key key_ = Key::Unknown;
};

} // namespace nk
