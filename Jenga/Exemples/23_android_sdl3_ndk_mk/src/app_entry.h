#pragma once

#include <string>
#include <utility>

enum class NkErrorCode {
    Ok = 0,
    SdlInitFailed = 1,
    WindowCreationFailed = 2,
    RendererCreationFailed = 3,
    TextureCreationFailed = 4,
    RuntimeFailed = 5,
};

class NkErrorHandler {
public:
    NkErrorHandler() = default;
    NkErrorHandler(NkErrorCode code, std::string message)
        : _code(code), _message(std::move(message)) {}

    static NkErrorHandler Success() {
        return NkErrorHandler(NkErrorCode::Ok, "");
    }

    static NkErrorHandler Failure(NkErrorCode code, const std::string& message) {
        return NkErrorHandler(code, message);
    }

    bool Ok() const {
        return _code == NkErrorCode::Ok;
    }

    NkErrorCode Code() const {
        return _code;
    }

    const std::string& Message() const {
        return _message;
    }

private:
    NkErrorCode _code = NkErrorCode::Ok;
    std::string _message;
};

inline int NkErrorToExitCode(const NkErrorHandler& error) {
    return static_cast<int>(error.Code());
}
