// =============================================================================
// NkCameraSystem.cpp — Implémentation complète et fonctionnelle
// =============================================================================

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "../../ThirdParty/stb/stb_image_write.h"

#include "NkCameraSystem.h"
#include "../NkPlatformDetect.h"
#include "../NkCamera2D.h"

// Sélection du backend selon la plateforme
#if defined(NKENTSEU_PLATFORM_WIN32) || defined(NKENTSEU_PLATFORM_UWP)
#   include "../../Platform/Win32/NkWin32CameraBackend.h"
    using PlatformCameraBackend = nkentseu::NkWin32CameraBackend;

#elif defined(NKENTSEU_PLATFORM_COCOA)
#   include "../../Platform/Cocoa/NkCocoaCameraBackend.h"
    using PlatformCameraBackend = nkentseu::NkCocoaCameraBackend;

#elif defined(NKENTSEU_PLATFORM_UIKIT)
#   include "../../Platform/UIKit/NkUIKitCameraBackend.h"
    using PlatformCameraBackend = nkentseu::NkUIKitCameraBackend;

#elif defined(NKENTSEU_PLATFORM_ANDROID)
#   include "../../Platform/Android/NkAndroidCameraBackend.h"
    using PlatformCameraBackend = nkentseu::NkAndroidCameraBackend;

#elif defined(NKENTSEU_PLATFORM_XCB) || defined(NKENTSEU_PLATFORM_XLIB)
#   include "../../Platform/Linux/NkLinuxCameraBackend.h"
    using PlatformCameraBackend = nkentseu::NkLinuxCameraBackend;

#elif defined(NKENTSEU_PLATFORM_WASM)
#   include "../../Platform/WASM/NkWASMCameraBackend.h"
    using PlatformCameraBackend = nkentseu::NkWASMCameraBackend;

#else
#   include "../../Platform/Noop/NkNoopCameraBackend.h"
    using PlatformCameraBackend = nkentseu::NkNoopCameraBackend;
#endif

#include <chrono>
#include <ctime>
#include <cmath>
#include <algorithm>

namespace nkentseu
{

// ===========================================================================
// NkCameraSystem — Init / Shutdown
// ===========================================================================

bool NkCameraSystem::Init()
{
    if (mReady) return true;
    mBackend = std::make_unique<PlatformCameraBackend>();
    if (!mBackend->Init()) {
        mBackend.reset();
        return false;
    }
    // Câbler le callback interne (thread de capture → OnFrame)
    mBackend->SetFrameCallback([this](const NkCameraFrame& f){ OnFrame(f); });
    mReady = true;
    return true;
}

void NkCameraSystem::Shutdown()
{
    if (!mReady) return;
    if (mBackend) {
        mBackend->StopVideoRecord();
        mBackend->StopStreaming();
        mBackend->Shutdown();
    }
    mBackend.reset();
    mReady = false;
    mRefCaptured = false;
    mVirtualCamera = nullptr;
}

// ===========================================================================
// Énumération
// ===========================================================================

std::vector<NkCameraDevice> NkCameraSystem::EnumerateDevices()
{
    if (!mReady) return {};
    return mBackend->EnumerateDevices();
}

void NkCameraSystem::SetHotPlugCallback(NkCameraHotPlugCallback cb)
{
    if (mReady) mBackend->SetHotPlugCallback(std::move(cb));
}

// ===========================================================================
// Streaming
// ===========================================================================

bool NkCameraSystem::StartStreaming(const NkCameraConfig& config)
{
    if (!mReady) return false;
    NkCameraConfig cfg = config;
    cfg.Resolve();
    mCurrentDeviceIndex = cfg.deviceIndex;
    // Recâbler le callback (peut avoir été écrasé lors d'un StopStreaming)
    mBackend->SetFrameCallback([this](const NkCameraFrame& f){ OnFrame(f); });
    return mBackend->StartStreaming(cfg);
}

void NkCameraSystem::StopStreaming()
{
    if (mReady) mBackend->StopStreaming();
}

NkCameraState NkCameraSystem::GetState() const
{
    return mReady ? mBackend->GetState() : NkCameraState::NK_CAM_STATE_CLOSED;
}

bool NkCameraSystem::IsStreaming() const
{
    auto s = GetState();
    return s == NkCameraState::NK_CAM_STATE_STREAMING
        || s == NkCameraState::NK_CAM_STATE_RECORDING;
}

void NkCameraSystem::SetFrameCallback(NkFrameCallback cb)
{
    std::lock_guard<std::mutex> lk(mFrameMutex);
    mUserCallback = std::move(cb);
}

bool NkCameraSystem::GetLastFrame(NkCameraFrame& out)
{
    std::lock_guard<std::mutex> lk(mFrameMutex);
    if (!mHasFrame) return false;
    out = mLastFrame;
    return true;
}

void NkCameraSystem::EnableFrameQueue(NkU32 maxSize)
{
    std::lock_guard<std::mutex> lk(mQueueMutex);
    mQueueEnabled = true;
    mMaxQueueSize = maxSize;
}

bool NkCameraSystem::DrainFrameQueue(NkCameraFrame& out)
{
    std::lock_guard<std::mutex> lk(mQueueMutex);
    if (mFrameQueue.empty()) return false;
    out = std::move(mFrameQueue.back());
    while (!mFrameQueue.empty()) mFrameQueue.pop();
    return true;
}

// ===========================================================================
// Capture photo
// ===========================================================================

bool NkCameraSystem::CapturePhoto(NkPhotoCaptureResult& out)
{
    if (!mReady) { out.success = false; out.errorMsg = "Camera not initialised"; return false; }
    return mBackend->CapturePhoto(out);
}

std::string NkCameraSystem::CapturePhotoToFile(const std::string& path)
{
    if (!mReady) return "";
    std::string p = path.empty() ? GenerateAutoPath("photo", "png") : path;
    return mBackend->CapturePhotoToFile(p) ? p : "";
}

// ===========================================================================
// Enregistrement vidéo
// ===========================================================================

bool NkCameraSystem::StartVideoRecord(const NkVideoRecordConfig& config)
{
    if (!mReady) return false;
    NkVideoRecordConfig cfg = config;
    if (cfg.outputPath.empty())
        cfg.outputPath = GenerateAutoPath("video", cfg.container);
    return mBackend->StartVideoRecord(cfg);
}

void  NkCameraSystem::StopVideoRecord()  { if (mReady) mBackend->StopVideoRecord(); }
bool  NkCameraSystem::IsRecording()  const { return mReady && mBackend->IsRecording(); }
float NkCameraSystem::GetRecordingDurationSeconds() const
{ return mReady ? mBackend->GetRecordingDurationSeconds() : 0.f; }

// ===========================================================================
// Contrôles
// ===========================================================================

bool NkCameraSystem::SetAutoFocus       (bool v) { return mReady && mBackend->SetAutoFocus(v); }
bool NkCameraSystem::SetAutoExposure    (bool v) { return mReady && mBackend->SetAutoExposure(v); }
bool NkCameraSystem::SetAutoWhiteBalance(bool v) { return mReady && mBackend->SetAutoWhiteBalance(v); }
bool NkCameraSystem::SetZoom            (float v){ return mReady && mBackend->SetZoom(v); }
bool NkCameraSystem::SetFlash           (bool v) { return mReady && mBackend->SetFlash(v); }
bool NkCameraSystem::SetTorch           (bool v) { return mReady && mBackend->SetTorch(v); }
bool NkCameraSystem::SetFocusPoint  (float x, float y)
{ return mReady && mBackend->SetFocusPoint(x, y); }

// ===========================================================================
// Informations session
// ===========================================================================

NkU32         NkCameraSystem::GetWidth()     const { return mReady ? mBackend->GetWidth()  : 0; }
NkU32         NkCameraSystem::GetHeight()    const { return mReady ? mBackend->GetHeight() : 0; }
NkU32         NkCameraSystem::GetFPS()       const { return mReady ? mBackend->GetFPS()    : 0; }
NkPixelFormat NkCameraSystem::GetFormat()    const
{ return mReady ? mBackend->GetFormat() : NkPixelFormat::NK_PIXEL_UNKNOWN; }
std::string   NkCameraSystem::GetLastError() const
{ return mReady ? mBackend->GetLastError() : "Camera system not initialised"; }

// ===========================================================================
// Callback interne — reçoit chaque frame du thread de capture
// ===========================================================================

void NkCameraSystem::OnFrame(const NkCameraFrame& frame)
{
    // Mettre à jour la dernière frame et appeler le callback utilisateur
    {
        std::lock_guard<std::mutex> lk(mFrameMutex);
        mLastFrame = frame;
        mHasFrame  = true;
        if (mUserCallback) mUserCallback(frame);
    }
    // Queue
    if (mQueueEnabled) {
        std::lock_guard<std::mutex> lk(mQueueMutex);
        if (mFrameQueue.size() >= mMaxQueueSize) mFrameQueue.pop();
        mFrameQueue.push(frame);
    }
}

// ===========================================================================
// MAPPING CAMÉRA VIRTUELLE ← CAMÉRA PHYSIQUE (IMU)
// ===========================================================================

void NkCameraSystem::SetVirtualCameraTarget(NkCamera2D* cam2D)
{
    mVirtualCamera = cam2D;
    mRefCaptured   = false; // réinitialiser la référence
}

void NkCameraSystem::SetVirtualCameraMapping(bool enable)
{
    mVirtualMappingEnabled = enable;
    if (enable) mRefCaptured = false; // prendre une nouvelle référence
}

bool NkCameraSystem::GetCurrentOrientation(NkCameraOrientation& out) const
{
    if (!mReady) return false;
    return const_cast<INkCameraBackend*>(mBackend.get())->GetOrientation(out);
}

void NkCameraSystem::UpdateVirtualCamera(float dt)
{
    if (!mVirtualMappingEnabled || !mVirtualCamera || !mReady) return;

    NkCameraOrientation orient;
    if (!mBackend->GetOrientation(orient)) return;

    // Capturer la pose de référence au premier appel
    if (!mRefCaptured) {
        mRefOrientation  = orient;
        mSmoothedYaw     = 0.f;
        mSmoothedPitch   = 0.f;
        mRefCaptured     = true;
        return;
    }

    // Différence par rapport à la référence
    float deltaYaw   = orient.yaw   - mRefOrientation.yaw;
    float deltaPitch = orient.pitch - mRefOrientation.pitch;

    // Inversion optionnelle
    if (mMapConfig.invertX) deltaYaw   = -deltaYaw;
    if (mMapConfig.invertY) deltaPitch = -deltaPitch;

    // Appliquer la sensibilité
    float targetYaw   = deltaYaw   * mMapConfig.yawSensitivity;
    float targetPitch = deltaPitch * mMapConfig.pitchSensitivity;

    // Lissage par interpolation (si activé)
    if (mMapConfig.smoothing) {
        float f = mMapConfig.smoothFactor;
        mSmoothedYaw   += (targetYaw   - mSmoothedYaw)   * f;
        mSmoothedPitch += (targetPitch - mSmoothedPitch) * f;
    } else {
        mSmoothedYaw   = targetYaw;
        mSmoothedPitch = targetPitch;
    }

    // Appliquer à la caméra virtuelle :
    // yaw   → translation horizontale (panoramique horizontal)
    // pitch → translation verticale   (panoramique vertical)
    // roll  → rotation de la caméra   (si souhaité)
    float panX = mSmoothedYaw   * mMapConfig.translationScale;
    float panY = mSmoothedPitch * mMapConfig.translationScale;

    if (mMapConfig.translationScale > 0.f) {
        // Mode translation : déplacer la caméra dans l'espace monde
        mVirtualCamera->SetPosition(panX, panY);
    } else {
        // Mode rotation seulement : utiliser la rotation de la caméra virtuelle
        // (yaw → rotation cam2D, car en 2D le seul axe de rotation est Z)
        mVirtualCamera->SetRotation(mSmoothedYaw + orient.roll);
    }
}

// ===========================================================================
// Conversions de format
// ===========================================================================

bool NkCameraSystem::ConvertToRGBA8(NkCameraFrame& frame)
{
    if (frame.format == NkPixelFormat::NK_PIXEL_RGBA8) return true;
    NkU32 w = frame.width, h = frame.height;
    std::vector<NkU8> out(w * h * 4);

    if (frame.format == NkPixelFormat::NK_PIXEL_BGRA8) {
        for (NkU32 i = 0; i < w * h; ++i) {
            out[i*4+0] = frame.data[i*4+2];
            out[i*4+1] = frame.data[i*4+1];
            out[i*4+2] = frame.data[i*4+0];
            out[i*4+3] = frame.data[i*4+3];
        }
        frame.data = std::move(out);
        frame.format = NkPixelFormat::NK_PIXEL_RGBA8;
        frame.stride = w * 4;
        return true;
    }

    if (frame.format == NkPixelFormat::NK_PIXEL_RGB8) {
        for (NkU32 i = 0; i < w * h; ++i) {
            out[i*4+0] = frame.data[i*3+0];
            out[i*4+1] = frame.data[i*3+1];
            out[i*4+2] = frame.data[i*3+2];
            out[i*4+3] = 255;
        }
        frame.data = std::move(out);
        frame.format = NkPixelFormat::NK_PIXEL_RGBA8;
        frame.stride = w * 4;
        return true;
    }

    if (frame.format == NkPixelFormat::NK_PIXEL_YUYV) {
        // YUYV packed: Y0 U0 Y1 V0
        for (NkU32 i = 0; i < w * h / 2; ++i) {
            float y0 = (float)frame.data[i*4+0] - 16.f;
            float cb = (float)frame.data[i*4+1] - 128.f;
            float y1 = (float)frame.data[i*4+2] - 16.f;
            float cr = (float)frame.data[i*4+3] - 128.f;
            auto cl = [](float v) -> NkU8 {
                return (NkU8)(v < 0 ? 0 : v > 255 ? 255 : v);
            };
            out[i*8+0] = cl(y0*1.164f + cr*1.596f);
            out[i*8+1] = cl(y0*1.164f - cb*0.391f - cr*0.813f);
            out[i*8+2] = cl(y0*1.164f + cb*2.018f);
            out[i*8+3] = 255;
            out[i*8+4] = cl(y1*1.164f + cr*1.596f);
            out[i*8+5] = cl(y1*1.164f - cb*0.391f - cr*0.813f);
            out[i*8+6] = cl(y1*1.164f + cb*2.018f);
            out[i*8+7] = 255;
        }
        frame.data = std::move(out);
        frame.format = NkPixelFormat::NK_PIXEL_RGBA8;
        frame.stride = w * 4;
        return true;
    }

    if (frame.format == NkPixelFormat::NK_PIXEL_NV12 ||
        frame.format == NkPixelFormat::NK_PIXEL_YUV420) {
        const NkU8* Y  = frame.data.data();
        const NkU8* UV = frame.data.data() + w * h;
        for (NkU32 row = 0; row < h; ++row) {
            for (NkU32 col = 0; col < w; ++col) {
                float y  = (float)Y[row * w + col] - 16.f;
                float u  = (float)UV[(row/2)*(w) + (col & ~1u)]     - 128.f;
                float v  = (float)UV[(row/2)*(w) + (col & ~1u) + 1] - 128.f;
                float r  = y * 1.164f + v * 1.596f;
                float g  = y * 1.164f - u * 0.391f - v * 0.813f;
                float b  = y * 1.164f + u * 2.018f;
                NkU32 idx = (row * w + col) * 4;
                out[idx+0] = (NkU8)(r < 0 ? 0 : r > 255 ? 255 : r);
                out[idx+1] = (NkU8)(g < 0 ? 0 : g > 255 ? 255 : g);
                out[idx+2] = (NkU8)(b < 0 ? 0 : b > 255 ? 255 : b);
                out[idx+3] = 255;
            }
        }
        frame.data = std::move(out);
        frame.format = NkPixelFormat::NK_PIXEL_RGBA8;
        frame.stride = w * 4;
        return true;
    }

    return false;
}

bool NkCameraSystem::SaveFrameToFile(const NkCameraFrame& frame,
                                     const std::string& path, int quality)
{
    if (!frame.IsValid()) return false;
    NkCameraFrame rgba = frame;
    if (!ConvertToRGBA8(rgba)) return false;

    std::string ext;
    auto dot = path.rfind('.');
    if (dot != std::string::npos) ext = path.substr(dot + 1);
    for (auto& c : ext) c = (char)std::tolower((unsigned char)c);

    if (ext == "png" || ext.empty())
        return stbi_write_png(path.c_str(), (int)rgba.width, (int)rgba.height,
                              4, rgba.data.data(), (int)rgba.stride) != 0;
    if (ext == "jpg" || ext == "jpeg")
        return stbi_write_jpg(path.c_str(), (int)rgba.width, (int)rgba.height,
                              4, rgba.data.data(), quality) != 0;
    if (ext == "bmp")
        return stbi_write_bmp(path.c_str(), (int)rgba.width, (int)rgba.height,
                              4, rgba.data.data()) != 0;
    // Fallback PNG
    return stbi_write_png(path.c_str(), (int)rgba.width, (int)rgba.height,
                          4, rgba.data.data(), (int)rgba.stride) != 0;
}

std::string NkCameraSystem::GenerateAutoPath(const std::string& prefix,
                                              const std::string& ext)
{
    auto now = std::chrono::system_clock::now();
    auto t   = std::chrono::system_clock::to_time_t(now);
    std::ostringstream ss;
    ss << prefix << "_"
       << std::put_time(std::localtime(&t), "%Y%m%d_%H%M%S")
       << "." << ext;
    return ss.str();
}

// ===========================================================================
// NkMultiCamera::Stream
// ===========================================================================

NkMultiCamera::Stream::Stream(NkU32 idx) : mDeviceIndex(idx)
{
    mBackend = std::make_unique<PlatformCameraBackend>();
    mBackend->Init();
    mBackend->SetFrameCallback([this](const NkCameraFrame& f){ OnFrame(f); });
}

NkMultiCamera::Stream::~Stream() { Stop(); if (mBackend) mBackend->Shutdown(); }

bool NkMultiCamera::Stream::Start(const NkCameraConfig& cfgIn)
{
    NkCameraConfig cfg = cfgIn;
    cfg.deviceIndex = mDeviceIndex;
    cfg.Resolve();
    mBackend->SetFrameCallback([this](const NkCameraFrame& f){ OnFrame(f); });
    return mBackend->StartStreaming(cfg);
}

void NkMultiCamera::Stream::Stop()
{
    if (mBackend) {
        mBackend->StopVideoRecord();
        mBackend->StopStreaming();
    }
}

void NkMultiCamera::Stream::OnFrame(const NkCameraFrame& f)
{
    { std::lock_guard<std::mutex> lk(mMutex); mLastFrame = f; mHasFrame = true; }
    if (mQueueEnabled) {
        std::lock_guard<std::mutex> lk(mQueueMutex);
        if (mQueue.size() >= mMaxQueue) mQueue.pop();
        mQueue.push(f);
    }
}

bool NkMultiCamera::Stream::GetLastFrame(NkCameraFrame& out)
{
    std::lock_guard<std::mutex> lk(mMutex);
    if (!mHasFrame) return false;
    out = mLastFrame; return true;
}

bool NkMultiCamera::Stream::DrainFrame(NkCameraFrame& out)
{
    std::lock_guard<std::mutex> lk(mQueueMutex);
    if (mQueue.empty()) return false;
    out = std::move(mQueue.back());
    while (!mQueue.empty()) mQueue.pop();
    return true;
}

void NkMultiCamera::Stream::EnableQueue(NkU32 sz)
{
    std::lock_guard<std::mutex> lk(mQueueMutex);
    mQueueEnabled = true; mMaxQueue = sz;
}

NkCameraState NkMultiCamera::Stream::GetState() const
{ return mBackend ? mBackend->GetState() : NkCameraState::NK_CAM_STATE_CLOSED; }

std::string NkMultiCamera::Stream::GetLastError() const
{ return mBackend ? mBackend->GetLastError() : "no backend"; }

bool NkMultiCamera::Stream::CapturePhotoToFile(const std::string& path)
{
    if (!mBackend) return false;
    std::string p = path.empty()
                  ? NkCameraSystem::GenerateAutoPath("photo_cam"
                    + std::to_string(mDeviceIndex), "png")
                  : path;
    return mBackend->CapturePhotoToFile(p);
}

// ===========================================================================
// NkMultiCamera
// ===========================================================================

NkMultiCamera::Stream& NkMultiCamera::Open(NkU32 deviceIndex,
                                            const NkCameraConfig& config)
{
    // Vérifier si déjà ouvert
    for (auto& s : mStreams)
        if (s->DeviceIndex() == deviceIndex)
            return *s;

    auto s = std::make_unique<Stream>(deviceIndex);
    s->Start(config);
    mStreams.push_back(std::move(s));
    return *mStreams.back();
}

void NkMultiCamera::Close(NkU32 deviceIndex)
{
    mStreams.erase(
        std::remove_if(mStreams.begin(), mStreams.end(),
            [deviceIndex](const std::unique_ptr<Stream>& s){
                return s->DeviceIndex() == deviceIndex;
            }),
        mStreams.end());
}

void NkMultiCamera::CloseAll() { mStreams.clear(); }

NkMultiCamera::Stream* NkMultiCamera::Get(NkU32 deviceIndex)
{
    for (auto& s : mStreams)
        if (s->DeviceIndex() == deviceIndex) return s.get();
    return nullptr;
}

} // namespace nkentseu
