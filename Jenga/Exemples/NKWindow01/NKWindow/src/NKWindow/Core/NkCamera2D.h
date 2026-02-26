#pragma once

#include "NkTypes.h"

#include <algorithm>

namespace nkentseu
{

class NkCamera2D
{
public:
    NkCamera2D() = default;
    NkCamera2D(NkU32 viewportWidth, NkU32 viewportHeight)
        : mViewport(viewportWidth, viewportHeight)
    {
    }

    void SetViewport(NkU32 width, NkU32 height) { mViewport = NkVec2u(width, height); }
    NkVec2u GetViewport() const { return mViewport; }

    void SetPosition(float x, float y) { mPosition = NkVec2f(x, y); }
    void Move(float dx, float dy)
    {
        mPosition.x += dx;
        mPosition.y += dy;
    }
    const NkVec2f& GetPosition() const { return mPosition; }

    void SetZoom(float zoom) { mZoom = std::max(0.01f, zoom); }
    float GetZoom() const { return mZoom; }

    void SetRotation(float degrees) { mRotationDegrees = degrees; }
    float GetRotation() const { return mRotationDegrees; }

    void SetShake(float amplitude, float durationSeconds)
    {
        mShakeAmplitude = std::max(0.0f, amplitude);
        mShakeRemainingSeconds = std::max(0.0f, durationSeconds);
    }

    void Update(float dtSeconds)
    {
        if (dtSeconds <= 0.0f || mShakeRemainingSeconds <= 0.0f)
            return;
        mShakeRemainingSeconds = std::max(0.0f, mShakeRemainingSeconds - dtSeconds);
    }

    float GetShakeRemainingSeconds() const { return mShakeRemainingSeconds; }
    float GetShakeAmplitude() const { return mShakeAmplitude; }

private:
    NkVec2f mPosition {0.0f, 0.0f};
    NkVec2u mViewport {0, 0};
    float   mZoom = 1.0f;
    float   mRotationDegrees = 0.0f;
    float   mShakeAmplitude = 0.0f;
    float   mShakeRemainingSeconds = 0.0f;
};

using Camera2D = NkCamera2D;

} // namespace nkentseu
