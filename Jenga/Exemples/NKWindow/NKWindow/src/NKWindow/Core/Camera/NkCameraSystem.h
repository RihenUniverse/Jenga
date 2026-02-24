#pragma once

#include "NkCameraTypes.h"

#include <vector>

namespace nkentseu
{

class NkCameraSystem
{
public:
    static NkCameraSystem& Instance()
    {
        static NkCameraSystem sInstance;
        return sInstance;
    }

    bool Init()
    {
        mReady = true;
        return true;
    }

    void Shutdown()
    {
        mReady = false;
        mDevices.clear();
    }

    bool IsReady() const { return mReady; }

    const std::vector<NkCameraDeviceInfo>& GetDevices() const { return mDevices; }

private:
    NkCameraSystem() = default;

    bool                            mReady = false;
    std::vector<NkCameraDeviceInfo> mDevices;
};

} // namespace nkentseu
