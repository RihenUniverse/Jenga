#pragma once

#include "app_entry.h"

#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

struct SDL_Window;
struct SDL_Renderer;
struct SDL_Texture;
typedef union SDL_Event SDL_Event;

struct AppVec3 {
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
};

struct AppColor {
    uint8_t r = 255;
    uint8_t g = 255;
    uint8_t b = 255;
};

struct AppStar {
    float x = 0.0f;
    float y = 0.0f;
    float pulse = 1.0f;
    float phase = 0.0f;
};

class Application {
public:
    explicit Application(std::vector<std::string> args);
    NkErrorHandler Start();
    NkErrorHandler HandleEvent(const SDL_Event& event);
    NkErrorHandler IterateFrame();
    void RequestQuit();
    bool IsRunning() const;
    void Close();

private:
    NkErrorHandler Initialize();
    void Shutdown();

    void ResizeBuffers(int width, int height);
    void ClearFrame(uint32_t color);
    void PresentFrame();

    bool Project(const AppVec3& point, float& sx, float& sy, float& depth) const;
    void PutPixel(int x, int y, float depth, const AppColor& color, float intensity = 1.0f);
    void DrawLine3D(const AppVec3& a, const AppVec3& b, const AppColor& color, int segments = 64);
    void DrawSphere(const AppVec3& center, float radius, const AppColor& color, const AppVec3& light_dir);

    void ResetView();
    void UpdateSimulation(float time_seconds);
    void UpdateCameraTransform();
    AppVec3 CurrentFollowPosition() const;
    bool PickFollowTarget(float mouse_x, float mouse_y, int& target_id) const;
    void ApplyFollowTarget(int target_id);

    void DrawStars(float time_seconds);
    void RenderSolarSystem(float time_seconds);

    double ResolveTestDurationSeconds() const;

    std::vector<std::string> _args;
    mutable std::mutex _loop_mutex;

    bool _started = false;
    bool _running = false;
    double _test_duration_seconds = -1.0;
    uint64_t _start_ticks_ns = 0;

    SDL_Window* _window = nullptr;
    SDL_Renderer* _renderer = nullptr;
    SDL_Texture* _texture = nullptr;

    int _width = 1280;
    int _height = 720;
    float _camera_distance = 18.0f;
    float _camera_yaw = 0.0f;
    float _camera_pitch = 0.18f;
    float _focal = 720.0f;

    AppVec3 _camera_position{0.0f, 0.0f, -4.0f};
    AppVec3 _camera_target{0.0f, 0.0f, 14.0f};
    AppVec3 _camera_forward{0.0f, 0.0f, 1.0f};
    AppVec3 _camera_right{1.0f, 0.0f, 0.0f};
    AppVec3 _camera_up{0.0f, 1.0f, 0.0f};

    bool _drag_look = false;
    float _last_mouse_x = 0.0f;
    float _last_mouse_y = 0.0f;

    bool _touch_rotate = false;
    uint64_t _touch_primary_id = 0;
    int _touch_active_count = 0;
    float _touch_primary_x = 0.0f;
    float _touch_primary_y = 0.0f;
    float _touch_down_x = 0.0f;
    float _touch_down_y = 0.0f;
    uint64_t _touch_down_time_ns = 0;
    float _last_tap_x = 0.0f;
    float _last_tap_y = 0.0f;
    uint64_t _last_tap_time_ns = 0;

    int _follow_target = 0;  // 0 none, 1 sun, 2 planet A, 3 planet B, 4 moon

    AppVec3 _sun_position{0.0f, 0.0f, 14.0f};
    AppVec3 _planet_a_position{0.0f, 0.0f, 14.0f};
    AppVec3 _planet_b_position{0.0f, 0.0f, 14.0f};
    AppVec3 _moon_position{0.0f, 0.0f, 14.0f};

    float _sun_radius = 2.0f;
    float _planet_a_radius = 0.9f;
    float _planet_b_radius = 0.6f;
    float _moon_radius = 0.34f;

    std::vector<uint32_t> _framebuffer;
    std::vector<float> _depthbuffer;
    std::vector<AppStar> _stars;
};
