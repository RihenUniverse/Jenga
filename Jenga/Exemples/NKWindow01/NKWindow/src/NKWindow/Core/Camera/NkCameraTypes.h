#pragma once

#include "../NkTypes.h"

#include <string>

namespace nkentseu
{

struct NkCameraDeviceInfo
{
    NkU32       id = 0;
    std::string name;
    bool        frontFacing = false;
};

struct NkCameraFrame
{
    NkU32         width = 0;
    NkU32         height = 0;
    NkU32         pitch = 0;
    NkPixelFormat pixelFormat = NkPixelFormat::NK_PIXEL_UNKNOWN;
    const NkU8*   data = nullptr;
    NkU64         timestampUs = 0;
};

} // namespace nkentseu
