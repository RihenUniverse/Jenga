#pragma once

#include <memory>
#include <vector>

#include "Event.hpp"
#include "Platform.hpp"
#include "Window.hpp"

namespace nk::detail {

class IWindowBackend {
public:
    virtual ~IWindowBackend() = default;

    virtual bool Create(const WindowConfig& config) = 0;
    virtual void PollEvents() = 0;
    virtual bool IsOpen() const = 0;
    virtual void Close() = 0;
    virtual int Width() const = 0;
    virtual int Height() const = 0;
    virtual const char* Name() const = 0;
};

class IEventBackend {
public:
    virtual ~IEventBackend() = default;

    virtual std::vector<std::unique_ptr<Event>> Pump() = 0;
    virtual const char* Name() const = 0;
};

std::unique_ptr<IWindowBackend> CreateWindowBackend(PlatformBackend platform);
std::unique_ptr<IEventBackend> CreateEventBackend(PlatformBackend platform);

std::unique_ptr<IWindowBackend> CreateWin32WindowBackend();
std::unique_ptr<IEventBackend> CreateWin32EventBackend();

std::unique_ptr<IWindowBackend> CreateXcbWindowBackend();
std::unique_ptr<IEventBackend> CreateXcbEventBackend();

std::unique_ptr<IWindowBackend> CreateXlibWindowBackend();
std::unique_ptr<IEventBackend> CreateXlibEventBackend();

std::unique_ptr<IWindowBackend> CreateAndroidWindowBackend();
std::unique_ptr<IEventBackend> CreateAndroidEventBackend();

std::unique_ptr<IWindowBackend> CreateEmscriptenWindowBackend();
std::unique_ptr<IEventBackend> CreateEmscriptenEventBackend();

std::unique_ptr<IWindowBackend> CreateIosWindowBackend();
std::unique_ptr<IEventBackend> CreateIosEventBackend();

std::unique_ptr<IWindowBackend> CreateMacosWindowBackend();
std::unique_ptr<IEventBackend> CreateMacosEventBackend();

std::unique_ptr<IWindowBackend> CreateHarmonyWindowBackend();
std::unique_ptr<IEventBackend> CreateHarmonyEventBackend();

} // namespace nk::detail
