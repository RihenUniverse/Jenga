#include "application.h"

#include <SDL3/SDL.h>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <random>
#include <string>

namespace {

constexpr float kPi = 3.14159265358979323846f;
constexpr float kNearClip = 0.05f;
constexpr float kFarDepth = 1.0e9f;
constexpr float kPitchLimit = 1.45f;
constexpr float kMinZoom = 3.5f;
constexpr float kMaxZoom = 70.0f;

float Clamp(const float value, const float min_value, const float max_value) {
    return std::max(min_value, std::min(max_value, value));
}

AppVec3 Add(const AppVec3& a, const AppVec3& b) {
    return AppVec3{a.x + b.x, a.y + b.y, a.z + b.z};
}

AppVec3 Sub(const AppVec3& a, const AppVec3& b) {
    return AppVec3{a.x - b.x, a.y - b.y, a.z - b.z};
}

AppVec3 Scale(const AppVec3& v, const float s) {
    return AppVec3{v.x * s, v.y * s, v.z * s};
}

float Dot(const AppVec3& a, const AppVec3& b) {
    return (a.x * b.x) + (a.y * b.y) + (a.z * b.z);
}

AppVec3 Cross(const AppVec3& a, const AppVec3& b) {
    return AppVec3{
        (a.y * b.z) - (a.z * b.y),
        (a.z * b.x) - (a.x * b.z),
        (a.x * b.y) - (a.y * b.x)
    };
}

float LengthSquared(const AppVec3& v) {
    return Dot(v, v);
}

AppVec3 Normalize(const AppVec3& v) {
    const float len_sq = LengthSquared(v);
    if (len_sq <= 1.0e-12f) {
        return AppVec3{0.0f, 0.0f, 0.0f};
    }
    const float inv_len = 1.0f / std::sqrt(len_sq);
    return Scale(v, inv_len);
}

uint32_t PackColor(const AppColor& color, float intensity) {
    intensity = Clamp(intensity, 0.0f, 1.0f);
    const uint8_t r = static_cast<uint8_t>(Clamp(static_cast<float>(color.r) * intensity, 0.0f, 255.0f));
    const uint8_t g = static_cast<uint8_t>(Clamp(static_cast<float>(color.g) * intensity, 0.0f, 255.0f));
    const uint8_t b = static_cast<uint8_t>(Clamp(static_cast<float>(color.b) * intensity, 0.0f, 255.0f));
    return (0xFFu << 24u) | (static_cast<uint32_t>(r) << 16u) | (static_cast<uint32_t>(g) << 8u) | static_cast<uint32_t>(b);
}

bool ParseDouble(const std::string& text, double& out_value) {
    if (text.empty()) {
        return false;
    }

    char* end_ptr = nullptr;
    const double value = std::strtod(text.c_str(), &end_ptr);
    if (end_ptr == text.c_str() || (end_ptr && *end_ptr != '\0') || !std::isfinite(value)) {
        return false;
    }

    out_value = value;
    return true;
}

void DrawDepthLine(
    std::vector<uint32_t>& framebuffer,
    std::vector<float>& depthbuffer,
    const int width,
    const int height,
    const float x0,
    const float y0,
    const float d0,
    const float x1,
    const float y1,
    const float d1,
    const AppColor& color,
    const float intensity
) {
    const float dx = x1 - x0;
    const float dy = y1 - y0;
    const int steps = std::max(1, static_cast<int>(std::ceil(std::max(std::fabs(dx), std::fabs(dy)))));
    const uint32_t packed = PackColor(color, intensity);

    for (int i = 0; i <= steps; ++i) {
        const float t = static_cast<float>(i) / static_cast<float>(steps);
        const int x = static_cast<int>(std::round(x0 + (dx * t)));
        const int y = static_cast<int>(std::round(y0 + (dy * t)));
        if (x < 0 || y < 0 || x >= width || y >= height) {
            continue;
        }

        const float depth = d0 + ((d1 - d0) * t);
        const std::size_t index = static_cast<std::size_t>(y) * static_cast<std::size_t>(width) + static_cast<std::size_t>(x);
        if (depth >= depthbuffer[index]) {
            continue;
        }
        depthbuffer[index] = depth;
        framebuffer[index] = packed;
    }
}

}  // namespace

Application::Application(std::vector<std::string> args)
    : _args(std::move(args)) {
    std::mt19937 rng(1337u);
    std::uniform_real_distribution<float> unit(0.0f, 1.0f);

    constexpr int kStarCount = 800;
    _stars.reserve(kStarCount);
    for (int i = 0; i < kStarCount; ++i) {
        _stars.push_back(AppStar{
            unit(rng),
            unit(rng),
            0.7f + (2.2f * unit(rng)),
            unit(rng) * (2.0f * kPi)
        });
    }

    ResetView();
}

NkErrorHandler Application::Start() {
    std::lock_guard<std::mutex> lock(_loop_mutex);

    if (_started) {
        _running = true;
        return NkErrorHandler::Success();
    }

    const NkErrorHandler init_result = Initialize();
    if (!init_result.Ok()) {
        Shutdown();
        return init_result;
    }

    _started = true;
    _running = true;
    _test_duration_seconds = ResolveTestDurationSeconds();
    _start_ticks_ns = static_cast<uint64_t>(SDL_GetTicksNS());
    return NkErrorHandler::Success();
}

NkErrorHandler Application::Initialize() {
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        return NkErrorHandler::Failure(NkErrorCode::SdlInitFailed, SDL_GetError());
    }

    const SDL_WindowFlags window_flags = SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIGH_PIXEL_DENSITY;
    if (!SDL_CreateWindowAndRenderer("Jenga SDL3 - Software Solar System", _width, _height, window_flags, &_window, &_renderer)) {
        return NkErrorHandler::Failure(NkErrorCode::WindowCreationFailed, SDL_GetError());
    }

    if (_window == nullptr || _renderer == nullptr) {
        return NkErrorHandler::Failure(NkErrorCode::RendererCreationFailed, "SDL_CreateWindowAndRenderer returned null objects");
    }

    int output_w = _width;
    int output_h = _height;
    if (!SDL_GetRenderOutputSize(_renderer, &output_w, &output_h)) {
        output_w = _width;
        output_h = _height;
    }

    ResizeBuffers(std::max(1, output_w), std::max(1, output_h));
    if (_texture == nullptr) {
        return NkErrorHandler::Failure(NkErrorCode::TextureCreationFailed, SDL_GetError());
    }

    SDL_Log("Software renderer initialized (no OpenGL).");
    return NkErrorHandler::Success();
}

NkErrorHandler Application::HandleEvent(const SDL_Event& event) {
    std::lock_guard<std::mutex> lock(_loop_mutex);

    if (!_started) {
        return NkErrorHandler::Failure(NkErrorCode::RuntimeFailed, "Application is not started");
    }

    switch (event.type) {
        case SDL_EVENT_QUIT:
        case SDL_EVENT_WINDOW_CLOSE_REQUESTED:
            _running = false;
            break;

        case SDL_EVENT_WINDOW_RESIZED:
        case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED: {
            int output_w = std::max(1, static_cast<int>(event.window.data1));
            int output_h = std::max(1, static_cast<int>(event.window.data2));
            if (_renderer != nullptr) {
                int rw = output_w;
                int rh = output_h;
                if (SDL_GetRenderOutputSize(_renderer, &rw, &rh)) {
                    output_w = std::max(1, rw);
                    output_h = std::max(1, rh);
                }
            }
            ResizeBuffers(output_w, output_h);
            break;
        }

        case SDL_EVENT_RENDER_TARGETS_RESET:
        case SDL_EVENT_RENDER_DEVICE_RESET: {
            int output_w = _width;
            int output_h = _height;
            if (_renderer != nullptr && SDL_GetRenderOutputSize(_renderer, &output_w, &output_h)) {
                output_w = std::max(1, output_w);
                output_h = std::max(1, output_h);
            }
            ResizeBuffers(output_w, output_h);
            break;
        }

        case SDL_EVENT_MOUSE_BUTTON_DOWN:
            if (event.button.which == SDL_TOUCH_MOUSEID) {
                break;
            }
            if (event.button.button == SDL_BUTTON_LEFT) {
                _drag_look = true;
                _last_mouse_x = event.button.x;
                _last_mouse_y = event.button.y;
            } else if (event.button.button == SDL_BUTTON_RIGHT) {
                int target_id = 0;
                if (PickFollowTarget(event.button.x, event.button.y, target_id)) {
                    ApplyFollowTarget(target_id);
                }
            }
            break;

        case SDL_EVENT_MOUSE_BUTTON_UP:
            if (event.button.which == SDL_TOUCH_MOUSEID) {
                break;
            }
            if (event.button.button == SDL_BUTTON_LEFT) {
                _drag_look = false;
            }
            break;

        case SDL_EVENT_MOUSE_MOTION:
            if (event.motion.which == SDL_TOUCH_MOUSEID) {
                break;
            }
            if (_drag_look) {
                const float dx = event.motion.x - _last_mouse_x;
                const float dy = event.motion.y - _last_mouse_y;
                _last_mouse_x = event.motion.x;
                _last_mouse_y = event.motion.y;

                _camera_yaw -= dx * 0.0070f;
                _camera_pitch += dy * 0.0050f;
                _camera_pitch = Clamp(_camera_pitch, -kPitchLimit, kPitchLimit);
            }
            break;

        case SDL_EVENT_MOUSE_WHEEL: {
            float wheel_y = event.wheel.y;
            if (event.wheel.direction == SDL_MOUSEWHEEL_FLIPPED) {
                wheel_y = -wheel_y;
            }
            _camera_distance *= std::pow(0.90f, wheel_y);
            _camera_distance = Clamp(_camera_distance, kMinZoom, kMaxZoom);
            break;
        }

        case SDL_EVENT_FINGER_DOWN: {
            ++_touch_active_count;
            if (_touch_primary_id == 0) {
                _touch_primary_id = static_cast<uint64_t>(event.tfinger.fingerID);
                _touch_primary_x = event.tfinger.x * static_cast<float>(_width);
                _touch_primary_y = event.tfinger.y * static_cast<float>(_height);
                _touch_down_x = _touch_primary_x;
                _touch_down_y = _touch_primary_y;
                _touch_down_time_ns = static_cast<uint64_t>(event.tfinger.timestamp);
                _touch_rotate = (_touch_active_count == 1);
            } else {
                _touch_rotate = false;
            }
            break;
        }

        case SDL_EVENT_FINGER_MOTION: {
            const uint64_t finger_id = static_cast<uint64_t>(event.tfinger.fingerID);
            if (_touch_rotate && _touch_active_count == 1 && finger_id == _touch_primary_id) {
                const float x = event.tfinger.x * static_cast<float>(_width);
                const float y = event.tfinger.y * static_cast<float>(_height);
                const float dx = x - _touch_primary_x;
                const float dy = y - _touch_primary_y;
                _touch_primary_x = x;
                _touch_primary_y = y;

                _camera_yaw -= dx * 0.0090f;
                _camera_pitch += dy * 0.0065f;
                _camera_pitch = Clamp(_camera_pitch, -kPitchLimit, kPitchLimit);
            }
            break;
        }

        case SDL_EVENT_FINGER_UP:
        case SDL_EVENT_FINGER_CANCELED: {
            if (_touch_active_count > 0) {
                --_touch_active_count;
            }

            const uint64_t finger_id = static_cast<uint64_t>(event.tfinger.fingerID);
            if (finger_id == _touch_primary_id) {
                const float up_x = event.tfinger.x * static_cast<float>(_width);
                const float up_y = event.tfinger.y * static_cast<float>(_height);
                const float travel = std::hypot(up_x - _touch_down_x, up_y - _touch_down_y);
                const uint64_t up_time_ns = static_cast<uint64_t>(event.tfinger.timestamp);
                const uint64_t press_duration_ns = (up_time_ns >= _touch_down_time_ns) ? (up_time_ns - _touch_down_time_ns) : 0u;
                if (travel < 16.0f && press_duration_ns <= 350000000ull) {
                    int target_id = 0;
                    bool picked = false;
                    if (PickFollowTarget(up_x, up_y, target_id)) {
                        ApplyFollowTarget(target_id);
                        _last_tap_time_ns = 0;
                        picked = true;
                    }
                    if (!picked) {
                        const bool double_tap_time_ok =
                            (_last_tap_time_ns != 0) && (up_time_ns >= _last_tap_time_ns) &&
                            ((up_time_ns - _last_tap_time_ns) <= 450000000ull);
                        const bool double_tap_distance_ok = std::hypot(up_x - _last_tap_x, up_y - _last_tap_y) <= 36.0f;
                        if (double_tap_time_ok && double_tap_distance_ok) {
                            ResetView();
                            _last_tap_time_ns = 0;
                        } else {
                            _last_tap_x = up_x;
                            _last_tap_y = up_y;
                            _last_tap_time_ns = up_time_ns;
                        }
                    }
                }

                _touch_primary_id = 0;
                _touch_rotate = false;
            }
            break;
        }

        case SDL_EVENT_PINCH_BEGIN:
            _touch_rotate = false;
            break;

        case SDL_EVENT_PINCH_UPDATE:
            if (event.pinch.scale > 0.001f) {
                _camera_distance /= event.pinch.scale;
                _camera_distance = Clamp(_camera_distance, kMinZoom, kMaxZoom);
            }
            break;

        case SDL_EVENT_PINCH_END:
            _touch_rotate = (_touch_active_count == 1 && _touch_primary_id != 0);
            break;

        case SDL_EVENT_KEY_DOWN:
            if (event.key.repeat) {
                break;
            }
            switch (event.key.key) {
                case SDLK_ESCAPE:
                    _running = false;
                    break;
                case SDLK_R:
                    ResetView();
                    break;
                case SDLK_0:
                    ApplyFollowTarget(0);
                    break;
                case SDLK_1:
                    ApplyFollowTarget(1);
                    break;
                case SDLK_2:
                    ApplyFollowTarget(2);
                    break;
                case SDLK_3:
                    ApplyFollowTarget(3);
                    break;
                case SDLK_4:
                    ApplyFollowTarget(4);
                    break;
                default:
                    break;
            }
            break;

        default:
            break;
    }

    return NkErrorHandler::Success();
}

NkErrorHandler Application::IterateFrame() {
    std::lock_guard<std::mutex> lock(_loop_mutex);

    if (!_started) {
        return NkErrorHandler::Failure(NkErrorCode::RuntimeFailed, "Application is not started");
    }
    if (!_running) {
        return NkErrorHandler::Success();
    }

    const double elapsed_seconds = static_cast<double>(SDL_GetTicksNS() - _start_ticks_ns) / 1.0e9;
    UpdateSimulation(static_cast<float>(elapsed_seconds));
    UpdateCameraTransform();

    ClearFrame(0xFF050812u);
    DrawStars(static_cast<float>(elapsed_seconds));
    RenderSolarSystem(static_cast<float>(elapsed_seconds));
    PresentFrame();

    if (_test_duration_seconds > 0.0 && elapsed_seconds >= _test_duration_seconds) {
        _running = false;
    }

    return NkErrorHandler::Success();
}

void Application::RequestQuit() {
    std::lock_guard<std::mutex> lock(_loop_mutex);
    _running = false;
}

bool Application::IsRunning() const {
    std::lock_guard<std::mutex> lock(_loop_mutex);
    return _running;
}

void Application::Close() {
    std::lock_guard<std::mutex> lock(_loop_mutex);
    _running = false;
    if (_started) {
        Shutdown();
        _started = false;
    }
}

void Application::Shutdown() {
    if (_texture != nullptr) {
        SDL_DestroyTexture(_texture);
        _texture = nullptr;
    }
    if (_renderer != nullptr) {
        SDL_DestroyRenderer(_renderer);
        _renderer = nullptr;
    }
    if (_window != nullptr) {
        SDL_DestroyWindow(_window);
        _window = nullptr;
    }
    SDL_Quit();
}

void Application::ResizeBuffers(int width, int height) {
    width = std::max(1, width);
    height = std::max(1, height);

    _width = width;
    _height = height;
    _focal = std::max(280.0f, static_cast<float>(std::min(_width, _height)) * 0.95f);

    _framebuffer.assign(static_cast<std::size_t>(_width) * static_cast<std::size_t>(_height), 0xFF000000u);
    _depthbuffer.assign(static_cast<std::size_t>(_width) * static_cast<std::size_t>(_height), kFarDepth);

    if (_texture != nullptr) {
        SDL_DestroyTexture(_texture);
        _texture = nullptr;
    }

    if (_renderer != nullptr) {
        _texture = SDL_CreateTexture(_renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_STREAMING, _width, _height);
    }
}

void Application::ClearFrame(uint32_t color) {
    std::fill(_framebuffer.begin(), _framebuffer.end(), color);
    std::fill(_depthbuffer.begin(), _depthbuffer.end(), kFarDepth);
}

void Application::PresentFrame() {
    if (_renderer == nullptr || _texture == nullptr || _framebuffer.empty()) {
        return;
    }

    if (!SDL_UpdateTexture(_texture, nullptr, _framebuffer.data(), _width * static_cast<int>(sizeof(uint32_t)))) {
        SDL_Log("SDL_UpdateTexture failed: %s", SDL_GetError());
        return;
    }
    if (!SDL_SetRenderDrawColor(_renderer, 0, 0, 0, 255)) {
        SDL_Log("SDL_SetRenderDrawColor failed: %s", SDL_GetError());
        return;
    }
    if (!SDL_RenderClear(_renderer)) {
        SDL_Log("SDL_RenderClear failed: %s", SDL_GetError());
        return;
    }
    if (!SDL_RenderTexture(_renderer, _texture, nullptr, nullptr)) {
        SDL_Log("SDL_RenderTexture failed: %s", SDL_GetError());
        return;
    }
    if (!SDL_RenderPresent(_renderer)) {
        SDL_Log("SDL_RenderPresent failed: %s", SDL_GetError());
    }
}

bool Application::Project(const AppVec3& point, float& sx, float& sy, float& depth) const {
    const AppVec3 rel = Sub(point, _camera_position);
    const float cam_x = Dot(rel, _camera_right);
    const float cam_y = Dot(rel, _camera_up);
    const float cam_z = Dot(rel, _camera_forward);
    if (cam_z <= kNearClip) {
        return false;
    }

    sx = (static_cast<float>(_width) * 0.5f) + ((cam_x * _focal) / cam_z);
    sy = (static_cast<float>(_height) * 0.5f) - ((cam_y * _focal) / cam_z);
    depth = cam_z;
    return true;
}

void Application::PutPixel(int x, int y, float depth, const AppColor& color, float intensity) {
    if (x < 0 || y < 0 || x >= _width || y >= _height) {
        return;
    }

    const std::size_t index = static_cast<std::size_t>(y) * static_cast<std::size_t>(_width) + static_cast<std::size_t>(x);
    if (depth >= _depthbuffer[index]) {
        return;
    }
    _depthbuffer[index] = depth;
    _framebuffer[index] = PackColor(color, intensity);
}

void Application::DrawLine3D(const AppVec3& a, const AppVec3& b, const AppColor& color, int segments) {
    segments = std::max(8, segments);

    bool has_previous = false;
    float prev_x = 0.0f;
    float prev_y = 0.0f;
    float prev_depth = 0.0f;

    for (int i = 0; i <= segments; ++i) {
        const float t = static_cast<float>(i) / static_cast<float>(segments);
        const AppVec3 p = AppVec3{
            a.x + ((b.x - a.x) * t),
            a.y + ((b.y - a.y) * t),
            a.z + ((b.z - a.z) * t)
        };

        float sx = 0.0f;
        float sy = 0.0f;
        float depth = 0.0f;
        if (!Project(p, sx, sy, depth)) {
            has_previous = false;
            continue;
        }

        if (has_previous) {
            DrawDepthLine(_framebuffer, _depthbuffer, _width, _height, prev_x, prev_y, prev_depth, sx, sy, depth, color, 1.0f);
        }
        prev_x = sx;
        prev_y = sy;
        prev_depth = depth;
        has_previous = true;
    }
}

void Application::DrawSphere(const AppVec3& center, float radius, const AppColor& color, const AppVec3& light_dir) {
    float center_x = 0.0f;
    float center_y = 0.0f;
    float center_depth = 0.0f;
    if (!Project(center, center_x, center_y, center_depth)) {
        return;
    }

    const float screen_radius = (_focal * radius) / std::max(center_depth, kNearClip);
    if (screen_radius < 0.75f) {
        return;
    }

    const int min_x = std::max(0, static_cast<int>(std::floor(center_x - screen_radius)));
    const int max_x = std::min(_width - 1, static_cast<int>(std::ceil(center_x + screen_radius)));
    const int min_y = std::max(0, static_cast<int>(std::floor(center_y - screen_radius)));
    const int max_y = std::min(_height - 1, static_cast<int>(std::ceil(center_y + screen_radius)));
    const float inv_r = 1.0f / screen_radius;

    AppVec3 normalized_light = Normalize(light_dir);
    if (LengthSquared(normalized_light) <= 1.0e-6f) {
        normalized_light = _camera_forward;
    }

    for (int y = min_y; y <= max_y; ++y) {
        for (int x = min_x; x <= max_x; ++x) {
            const float dx = ((static_cast<float>(x) + 0.5f) - center_x) * inv_r;
            const float dy = ((static_cast<float>(y) + 0.5f) - center_y) * inv_r;
            const float rr = (dx * dx) + (dy * dy);
            if (rr > 1.0f) {
                continue;
            }

            const float nz = std::sqrt(std::max(0.0f, 1.0f - rr));
            const AppVec3 normal = Normalize(Add(Add(Scale(_camera_right, dx), Scale(_camera_up, -dy)), Scale(_camera_forward, nz)));
            const float diffuse = std::max(0.0f, Dot(normal, normalized_light));
            const float intensity = 0.18f + (0.82f * diffuse);
            const float depth = center_depth - (nz * radius);
            PutPixel(x, y, depth, color, intensity);
        }
    }
}

void Application::ResetView() {
    _camera_distance = 18.0f;
    _camera_yaw = 0.0f;
    _camera_pitch = 0.18f;
    _follow_target = 0;
    _camera_target = _sun_position;
    UpdateCameraTransform();
}

void Application::UpdateSimulation(float time_seconds) {
    const float sun_z = 14.0f;
    _sun_position = AppVec3{0.0f, 0.0f, sun_z};

    const float orbit_a = 5.0f;
    const float angle_a = time_seconds * 0.70f;
    _planet_a_position = AppVec3{
        _sun_position.x + (std::cos(angle_a) * orbit_a),
        std::sin(time_seconds * 0.95f) * 0.36f,
        _sun_position.z + (std::sin(angle_a) * orbit_a)
    };

    const float orbit_b = 8.1f;
    const float angle_b = (time_seconds * 0.38f) + 1.1f;
    _planet_b_position = AppVec3{
        _sun_position.x + (std::cos(angle_b) * orbit_b),
        std::sin((time_seconds * 0.55f) + 1.0f) * 0.62f,
        _sun_position.z + (std::sin(angle_b) * orbit_b)
    };

    const float moon_orbit = 1.7f;
    const float moon_angle = time_seconds * 2.25f;
    _moon_position = AppVec3{
        _planet_a_position.x + (std::cos(moon_angle) * moon_orbit),
        _planet_a_position.y + (std::sin(moon_angle * 1.2f) * 0.22f),
        _planet_a_position.z + (std::sin(moon_angle) * moon_orbit)
    };
}

void Application::UpdateCameraTransform() {
    if (_follow_target != 0) {
        _camera_target = CurrentFollowPosition();
    }

    _camera_pitch = Clamp(_camera_pitch, -kPitchLimit, kPitchLimit);
    _camera_distance = Clamp(_camera_distance, kMinZoom, kMaxZoom);

    const float cp = std::cos(_camera_pitch);
    const float sp = std::sin(_camera_pitch);
    const float cy = std::cos(_camera_yaw);
    const float sy = std::sin(_camera_yaw);

    _camera_forward = Normalize(AppVec3{sy * cp, -sp, cy * cp});
    const AppVec3 world_up{0.0f, 1.0f, 0.0f};
    _camera_right = Normalize(Cross(world_up, _camera_forward));
    if (LengthSquared(_camera_right) < 1.0e-8f) {
        _camera_right = AppVec3{1.0f, 0.0f, 0.0f};
    }
    _camera_up = Normalize(Cross(_camera_forward, _camera_right));

    _camera_position = Sub(_camera_target, Scale(_camera_forward, _camera_distance));
}

AppVec3 Application::CurrentFollowPosition() const {
    switch (_follow_target) {
        case 1:
            return _sun_position;
        case 2:
            return _planet_a_position;
        case 3:
            return _planet_b_position;
        case 4:
            return _moon_position;
        default:
            return _camera_target;
    }
}

bool Application::PickFollowTarget(float mouse_x, float mouse_y, int& target_id) const {
    target_id = 0;

    struct PickCandidate {
        int id;
        AppVec3 position;
        float radius;
    };

    const PickCandidate candidates[] = {
        PickCandidate{1, _sun_position, _sun_radius},
        PickCandidate{2, _planet_a_position, _planet_a_radius},
        PickCandidate{3, _planet_b_position, _planet_b_radius},
        PickCandidate{4, _moon_position, _moon_radius}
    };

    bool found = false;
    float best_depth = std::numeric_limits<float>::max();
    for (const PickCandidate& candidate : candidates) {
        float sx = 0.0f;
        float sy = 0.0f;
        float depth = 0.0f;
        if (!Project(candidate.position, sx, sy, depth)) {
            continue;
        }

        const float projected_radius = std::max(6.0f, (_focal * candidate.radius) / std::max(depth, kNearClip));
        const float dx = mouse_x - sx;
        const float dy = mouse_y - sy;
        if ((dx * dx) + (dy * dy) > (projected_radius * projected_radius)) {
            continue;
        }

        if (depth < best_depth) {
            best_depth = depth;
            target_id = candidate.id;
            found = true;
        }
    }

    return found;
}

void Application::ApplyFollowTarget(int target_id) {
    if (target_id < 0 || target_id > 4) {
        return;
    }

    _follow_target = target_id;
    if (_follow_target == 0) {
        _camera_target = _sun_position;
    } else {
        _camera_target = CurrentFollowPosition();
    }
}

void Application::DrawStars(float time_seconds) {
    if (_stars.empty()) {
        return;
    }

    for (const AppStar& star : _stars) {
        const int x = static_cast<int>(star.x * static_cast<float>(_width - 1));
        const int y = static_cast<int>(star.y * static_cast<float>(_height - 1));
        const float blink = 0.35f + (0.65f * (0.5f + (0.5f * std::sin((time_seconds * star.pulse) + star.phase))));
        const AppColor color{220, 230, 255};
        PutPixel(x, y, kFarDepth * 0.98f, color, blink);
        PutPixel(x + 1, y, kFarDepth * 0.98f, color, blink * 0.35f);
        PutPixel(x - 1, y, kFarDepth * 0.98f, color, blink * 0.35f);
        PutPixel(x, y + 1, kFarDepth * 0.98f, color, blink * 0.35f);
        PutPixel(x, y - 1, kFarDepth * 0.98f, color, blink * 0.35f);
    }
}

void Application::RenderSolarSystem(float time_seconds) {
    (void)time_seconds;

    const AppColor orbit_color{68, 82, 122};
    const int orbit_segments = 96;

    for (int i = 0; i < orbit_segments; ++i) {
        const float a0 = (2.0f * kPi * static_cast<float>(i)) / static_cast<float>(orbit_segments);
        const float a1 = (2.0f * kPi * static_cast<float>(i + 1)) / static_cast<float>(orbit_segments);

        const AppVec3 p0 = AppVec3{
            _sun_position.x + (std::cos(a0) * 5.0f),
            _sun_position.y,
            _sun_position.z + (std::sin(a0) * 5.0f)
        };
        const AppVec3 p1 = AppVec3{
            _sun_position.x + (std::cos(a1) * 5.0f),
            _sun_position.y,
            _sun_position.z + (std::sin(a1) * 5.0f)
        };
        DrawLine3D(p0, p1, orbit_color, 10);

        const AppVec3 q0 = AppVec3{
            _sun_position.x + (std::cos(a0) * 8.1f),
            _sun_position.y,
            _sun_position.z + (std::sin(a0) * 8.1f)
        };
        const AppVec3 q1 = AppVec3{
            _sun_position.x + (std::cos(a1) * 8.1f),
            _sun_position.y,
            _sun_position.z + (std::sin(a1) * 8.1f)
        };
        DrawLine3D(q0, q1, orbit_color, 10);

        const AppVec3 m0 = AppVec3{
            _planet_a_position.x + (std::cos(a0) * 1.7f),
            _planet_a_position.y,
            _planet_a_position.z + (std::sin(a0) * 1.7f)
        };
        const AppVec3 m1 = AppVec3{
            _planet_a_position.x + (std::cos(a1) * 1.7f),
            _planet_a_position.y,
            _planet_a_position.z + (std::sin(a1) * 1.7f)
        };
        DrawLine3D(m0, m1, AppColor{80, 96, 124}, 10);
    }

    const AppVec3 sun_light = Normalize(Sub(_camera_position, _sun_position));
    const AppVec3 light_to_a = Normalize(Sub(_sun_position, _planet_a_position));
    const AppVec3 light_to_b = Normalize(Sub(_sun_position, _planet_b_position));
    const AppVec3 light_to_moon = Normalize(Sub(_sun_position, _moon_position));

    DrawSphere(_sun_position, _sun_radius, AppColor{255, 210, 96}, sun_light);
    DrawSphere(_planet_a_position, _planet_a_radius, AppColor{92, 172, 255}, light_to_a);
    DrawSphere(_planet_b_position, _planet_b_radius, AppColor{255, 132, 108}, light_to_b);
    DrawSphere(_moon_position, _moon_radius, AppColor{226, 226, 218}, light_to_moon);

    if (_follow_target != 0) {
        const AppVec3 focus = CurrentFollowPosition();
        const AppColor marker{255, 245, 132};
        DrawLine3D(Add(focus, AppVec3{-0.5f, 0.0f, 0.0f}), Add(focus, AppVec3{0.5f, 0.0f, 0.0f}), marker, 12);
        DrawLine3D(Add(focus, AppVec3{0.0f, -0.5f, 0.0f}), Add(focus, AppVec3{0.0f, 0.5f, 0.0f}), marker, 12);
        DrawLine3D(Add(focus, AppVec3{0.0f, 0.0f, -0.5f}), Add(focus, AppVec3{0.0f, 0.0f, 0.5f}), marker, 12);
    }
}

double Application::ResolveTestDurationSeconds() const {
    for (std::size_t i = 0; i < _args.size(); ++i) {
        const std::string& arg = _args[i];
        constexpr const char* kPrefix = "--test-seconds=";
        if (arg.rfind(kPrefix, 0) == 0) {
            double parsed = -1.0;
            if (ParseDouble(arg.substr(std::char_traits<char>::length(kPrefix)), parsed)) {
                return parsed;
            }
        }
        if (arg == "--test-seconds" && (i + 1) < _args.size()) {
            double parsed = -1.0;
            if (ParseDouble(_args[i + 1], parsed)) {
                return parsed;
            }
        }
    }

    const char* env_seconds = std::getenv("JENGA_SDL3_TEST_SECONDS");
    if (env_seconds != nullptr) {
        double parsed = -1.0;
        if (ParseDouble(env_seconds, parsed)) {
            return parsed;
        }
    }

    return -1.0;
}
