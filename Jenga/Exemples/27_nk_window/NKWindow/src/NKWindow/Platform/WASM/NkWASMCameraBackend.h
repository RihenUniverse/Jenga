#pragma once
// =============================================================================
// NkWASMCameraBackend.h — WebAssembly: getUserMedia + DeviceOrientation API
// COMPLET ET FONCTIONNEL
// GetOrientation: window.DeviceOrientationEvent (alpha/beta/gamma)
// =============================================================================
#include "../../Core/Camera/INkCameraBackend.h"
#ifdef __EMSCRIPTEN__
#  include <emscripten.h>
#  include <emscripten/html5.h>
#endif
#include <mutex>
#include <atomic>
#include <chrono>
#include <string>
#include <vector>
#include <cmath>

namespace nkentseu
{

class NkWASMCameraBackend : public INkCameraBackend
{
public:
    NkWASMCameraBackend()  { sInstance = this; }
    ~NkWASMCameraBackend() override { Shutdown(); sInstance = nullptr; }

    // ------------------------------------------------------------------
    bool Init() override
    {
#ifdef __EMSCRIPTEN__
        EM_ASM({
            if (window._NkCam) return;
            window._NkCam = {
                stream: null, video: null, canvas: null, ctx: null,
                mediaRecorder: null, chunks: [],
                w: 0, h: 0, fps: 30,
                lastRGBA: null, frameReady: false,
                streaming: false, recording: false,
                orient: { alpha:0, beta:0, gamma:0 },

                setup: function(w,h,fps) {
                    this.w=w; this.h=h; this.fps=fps;
                    this.video  = document.createElement('video');
                    this.canvas = document.createElement('canvas');
                    this.canvas.width=w; this.canvas.height=h;
                    this.ctx = this.canvas.getContext('2d');
                    this.video.addEventListener('loadedmetadata', () => {
                        this.canvas.width  = this.video.videoWidth  || w;
                        this.canvas.height = this.video.videoHeight || h;
                        this.w=this.canvas.width; this.h=this.canvas.height;
                    });
                    // DeviceOrientation (IMU)
                    window.addEventListener('deviceorientation', e => {
                        this.orient.alpha = e.alpha || 0; // yaw [0,360]
                        this.orient.beta  = e.beta  || 0; // pitch [-180,180]
                        this.orient.gamma = e.gamma || 0; // roll [-90,90]
                    }, true);
                },

                start: function(deviceId, facing) {
                    const constraints = {
                        video: deviceId
                            ? { deviceId: { exact: deviceId },
                                width:{ideal:this.w}, height:{ideal:this.h},
                                frameRate:{ideal:this.fps} }
                            : { facingMode: facing||'environment',
                                width:{ideal:this.w}, height:{ideal:this.h},
                                frameRate:{ideal:this.fps} }
                    };
                    navigator.mediaDevices.getUserMedia(constraints)
                        .then(stream => {
                            this.stream = stream;
                            this.video.srcObject = stream;
                            this.video.play();
                            this.streaming = true;
                            Module._NkWASMStreamOK();
                            this._loop();
                        })
                        .catch(e => {
                            const msg = e.message || 'getUserMedia failed';
                            const sz  = Module.lengthBytesUTF8(msg)+1;
                            const ptr = Module._malloc(sz);
                            Module.stringToUTF8(msg, ptr, sz);
                            Module._NkWASMStreamErr(ptr);
                            Module._free(ptr);
                        });
                },

                _loop: function() {
                    if (!this.streaming) return;
                    if (this.video.readyState >= 2) {
                        this.ctx.drawImage(this.video,0,0,this.canvas.width,this.canvas.height);
                        const d = this.ctx.getImageData(0,0,this.canvas.width,this.canvas.height);
                        this.lastRGBA   = d.data;
                        this.frameReady = true;
                        Module._NkWASMFrame(this.canvas.width, this.canvas.height, d.data.length);
                    }
                    setTimeout(()=>this._loop(), 1000/this.fps);
                },

                stop: function() {
                    this.streaming = false;
                    if (this.stream) this.stream.getTracks().forEach(t=>t.stop());
                    this.stream = null;
                },

                grabRGBA: function(ptr, max) {
                    if (!this.lastRGBA) return 0;
                    const len = Math.min(this.lastRGBA.length, max);
                    Module.HEAPU8.set(this.lastRGBA.subarray(0,len), ptr);
                    this.frameReady = false;
                    return len;
                },

                startRecord: function(mime) {
                    if (!this.stream) return false;
                    this.chunks = [];
                    let opts = {};
                    const types = [mime,'video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'];
                    for (const t of types)
                        if (MediaRecorder.isTypeSupported(t)) { opts={mimeType:t}; break; }
                    this.mediaRecorder = new MediaRecorder(this.stream, opts);
                    this.mediaRecorder.ondataavailable = e => {
                        if (e.data.size>0) this.chunks.push(e.data);
                    };
                    this.mediaRecorder.start(100);
                    this.recording = true;
                    return true;
                },

                stopRecord: function(filename) {
                    if (!this.mediaRecorder) return;
                    this.mediaRecorder.onstop = () => {
                        const blob=new Blob(this.chunks,{type:this.mediaRecorder.mimeType});
                        const url=URL.createObjectURL(blob);
                        const a=document.createElement('a');
                        a.href=url; a.download=filename||'video.webm'; a.click();
                        URL.revokeObjectURL(url);
                    };
                    this.mediaRecorder.stop();
                    this.recording = false;
                },

                getOrientation: function(ptr) {
                    // Écrire 3 floats: alpha(yaw), beta(pitch), gamma(roll)
                    Module.HEAPF32[ptr>>2]   = this.orient.alpha;
                    Module.HEAPF32[(ptr+4)>>2]= this.orient.beta;
                    Module.HEAPF32[(ptr+8)>>2]= this.orient.gamma;
                },

                enumDevices: function(cb) {
                    if (!navigator.mediaDevices.enumerateDevices) {
                        Module.ccall(cb,'v',['string'],['[]']); return;
                    }
                    navigator.mediaDevices.enumerateDevices().then(devs => {
                        const cams = devs.filter(d=>d.kind==='videoinput').map((d,i)=>({
                            index:i, id:d.deviceId, label:d.label||('Camera '+i),
                            facing: (d.label.toLowerCase().includes('front')||
                                     d.label.toLowerCase().includes('selfie')) ? 'front':'back'
                        }));
                        const json = JSON.stringify(cams);
                        const sz=Module.lengthBytesUTF8(json)+1;
                        const p=Module._malloc(sz);
                        Module.stringToUTF8(json,p,sz);
                        Module.ccall(cb,'v',['number'],[p]);
                        Module._free(p);
                    });
                }
            };
        });
#endif
        return true;
    }

    void Shutdown() override { StopStreaming(); }

    // ------------------------------------------------------------------
    // Énumération — asynchrone, résultat mis en cache
    // ------------------------------------------------------------------
    std::vector<NkCameraDevice> EnumerateDevices() override
    {
#ifdef __EMSCRIPTEN__
        if (mCachedDevices.empty()) {
            EM_ASM({ window._NkCam.enumDevices('_NkWASMDeviceList'); });
            // La liste sera peuplée via _NkWASMDeviceList callback
            // Pour l'appel synchrone, retourner ce qui est déjà caché
        }
#endif
        return mCachedDevices;
    }

    void SetHotPlugCallback(NkCameraHotPlugCallback cb) override { mHotPlugCb=std::move(cb); }

    // ------------------------------------------------------------------
    bool StartStreaming(const NkCameraConfig& config) override
    {
#ifdef __EMSCRIPTEN__
        mWidth  = config.width  ? config.width  : 1280;
        mHeight = config.height ? config.height : 720;
        mFPS    = config.fps    ? config.fps    : 30;

        EM_ASM({ window._NkCam.setup($0,$1,$2); }, mWidth, mHeight, mFPS);

        // Sélectionner le device par index si disponible
        std::string deviceId;
        if (config.deviceIndex < mCachedDevices.size())
            deviceId = mCachedDevices[config.deviceIndex].id;

        const char* facing = (config.facing==NkCameraFacing::NK_CAMERA_FACING_FRONT)
                           ? "user" : "environment";
        bool isFront       = config.facing==NkCameraFacing::NK_CAMERA_FACING_FRONT;

        EM_ASM({
            const devId   = $0 ? UTF8ToString($0) : null;
            const facing  = UTF8ToString($1);
            window._NkCam.start(devId, facing);
        }, deviceId.empty() ? nullptr : deviceId.c_str(), facing);

        mState = NkCameraState::NK_CAM_STATE_OPENING;
        return true; // résultat asynchrone via _NkWASMStreamOK / _NkWASMStreamErr
#else
        return false;
#endif
    }

    void StopStreaming() override
    {
        StopVideoRecord();
#ifdef __EMSCRIPTEN__
        EM_ASM({ if(window._NkCam) window._NkCam.stop(); });
#endif
        mState = NkCameraState::NK_CAM_STATE_CLOSED;
    }

    NkCameraState GetState() const override { return mState; }
    void SetFrameCallback(NkFrameCallback cb) override { mFrameCb=std::move(cb); }

    bool GetLastFrame(NkCameraFrame& out) override {
        std::lock_guard<std::mutex> lk(mMutex);
        if (!mHasFrame) return false; out=mLastFrame; return true;
    }

    // ------------------------------------------------------------------
    bool CapturePhoto(NkPhotoCaptureResult& res) override {
        std::lock_guard<std::mutex> lk(mMutex);
        if (!mHasFrame){res.success=false;res.errorMsg="No frame";return false;}
        res.frame=mLastFrame; res.success=true; return true;
    }

    bool CapturePhotoToFile(const std::string& path) override {
#ifdef __EMSCRIPTEN__
        std::string fn = path.empty() ? "photo.png" : path;
        EM_ASM({
            const fn=UTF8ToString($0);
            const c=window._NkCam.canvas; if(!c) return;
            const a=document.createElement('a');
            a.href=c.toDataURL('image/png'); a.download=fn; a.click();
        }, fn.c_str());
        return true;
#else
        return false;
#endif
    }

    // ------------------------------------------------------------------
    bool StartVideoRecord(const NkVideoRecordConfig& config) override {
#ifdef __EMSCRIPTEN__
        std::string mime = (config.container=="mp4")
                         ? "video/mp4;codecs=avc1" : "video/webm;codecs=vp9";
        bool ok = (bool)EM_ASM_INT({
            return window._NkCam.startRecord(UTF8ToString($0)) ? 1 : 0;
        }, mime.c_str());
        if (!ok) { mLastError="MediaRecorder start failed"; return false; }
        mRecordPath  = config.outputPath.empty() ? "video.webm" : config.outputPath;
        mRecordStart = std::chrono::steady_clock::now();
        mRecording   = true;
        mState       = NkCameraState::NK_CAM_STATE_RECORDING;
        return true;
#else
        return false;
#endif
    }

    void StopVideoRecord() override {
#ifdef __EMSCRIPTEN__
        if (!mRecording) return;
        EM_ASM({ window._NkCam.stopRecord(UTF8ToString($0)); }, mRecordPath.c_str());
#endif
        mRecording = false;
        if (mState==NkCameraState::NK_CAM_STATE_RECORDING)
            mState = NkCameraState::NK_CAM_STATE_STREAMING;
    }

    bool  IsRecording() const override { return mRecording; }
    float GetRecordingDurationSeconds() const override {
        if (!mRecording) return 0.f;
        return std::chrono::duration<float>(
            std::chrono::steady_clock::now()-mRecordStart).count();
    }

    // ------------------------------------------------------------------
    // GetOrientation — DeviceOrientation API (gyro natif navigateur)
    // ------------------------------------------------------------------
    bool GetOrientation(NkCameraOrientation& out) override {
#ifdef __EMSCRIPTEN__
        float buf[3] = {0,0,0};
        EM_ASM({
            if (window._NkCam) window._NkCam.getOrientation($0);
        }, buf);
        out.yaw   = buf[0]; // alpha [0, 360]
        out.pitch = buf[1]; // beta  [-180, 180]
        out.roll  = buf[2]; // gamma [-90, 90]
        out.accelX = out.accelY = out.accelZ = 0.f;
        return true;
#else
        return false;
#endif
    }

    NkU32 GetWidth()  const override { return mWidth;  }
    NkU32 GetHeight() const override { return mHeight; }
    NkU32 GetFPS()    const override { return mFPS;    }
    NkPixelFormat GetFormat() const override { return NkPixelFormat::NK_PIXEL_RGBA8; }
    std::string GetLastError() const override { return mLastError; }

    // ------------------------------------------------------------------
    // Callbacks C exportés pour JS
    // ------------------------------------------------------------------
    static void _OnFrame(int w, int h, int nbytes) {
        if (!sInstance) return;
#ifdef __EMSCRIPTEN__
        std::vector<NkU8> buf((size_t)nbytes);
        int copied = EM_ASM_INT({
            return window._NkCam.grabRGBA($0,$1);
        }, buf.data(), nbytes);
        if (copied<=0) return;
        buf.resize((size_t)copied);

        NkCameraFrame frame;
        frame.width=(NkU32)w; frame.height=(NkU32)h;
        frame.format=NkPixelFormat::NK_PIXEL_RGBA8;
        frame.stride=(NkU32)w*4;
        frame.frameIndex=sInstance->mFrameIdx++;
        frame.data=std::move(buf);

        { std::lock_guard<std::mutex> lk(sInstance->mMutex);
          sInstance->mLastFrame=frame; sInstance->mHasFrame=true; }
        if (sInstance->mFrameCb) sInstance->mFrameCb(frame);
#endif
    }
    static void _OnStreamOK() {
        if (sInstance) sInstance->mState=NkCameraState::NK_CAM_STATE_STREAMING;
    }
    static void _OnStreamErr(const char* msg) {
        if (!sInstance) return;
        sInstance->mLastError = msg ? msg : "getUserMedia failed";
        sInstance->mState = NkCameraState::NK_CAM_STATE_ERROR;
    }
    static void _OnDeviceList(const char* json) {
        if (!sInstance || !json) return;
        // Parser JSON minimaliste pour remplir mCachedDevices
        sInstance->mCachedDevices.clear();
        // Format: [{"index":0,"id":"xxx","label":"yyy","facing":"back"}, ...]
        std::string s(json);
        size_t pos=0;
        NkU32 idx=0;
        while ((pos=s.find("\"id\":",pos))!=std::string::npos) {
            NkCameraDevice dev;
            dev.index=idx++;
            size_t q1=s.find('"',pos+5)+1;
            size_t q2=s.find('"',q1);
            dev.id=s.substr(q1,q2-q1);
            size_t lp=s.find("\"label\":",pos);
            if (lp!=std::string::npos) {
                size_t l1=s.find('"',lp+8)+1;
                size_t l2=s.find('"',l1);
                dev.name=s.substr(l1,l2-l1);
            }
            size_t fp=s.find("\"facing\":",pos);
            dev.facing=NkCameraFacing::NK_CAMERA_FACING_EXTERNAL;
            if (fp!=std::string::npos) {
                size_t f1=s.find('"',fp+9)+1;
                size_t f2=s.find('"',f1);
                std::string fstr=s.substr(f1,f2-f1);
                if (fstr=="front") dev.facing=NkCameraFacing::NK_CAMERA_FACING_FRONT;
                else if (fstr=="back") dev.facing=NkCameraFacing::NK_CAMERA_FACING_BACK;
            }
            sInstance->mCachedDevices.push_back(dev);
            pos=q2+1;
        }
    }

private:
    static NkWASMCameraBackend* sInstance;

    NkCameraState mState=NkCameraState::NK_CAM_STATE_CLOSED;
    NkU32 mWidth=0, mHeight=0, mFPS=30, mFrameIdx=0;
    std::string mLastError;
    bool mRecording=false;
    std::string mRecordPath;

    std::mutex    mMutex;
    NkCameraFrame mLastFrame;
    bool          mHasFrame=false;

    NkFrameCallback         mFrameCb;
    NkCameraHotPlugCallback mHotPlugCb;
    std::vector<NkCameraDevice> mCachedDevices;
    std::chrono::steady_clock::time_point mRecordStart;
};

inline NkWASMCameraBackend* NkWASMCameraBackend::sInstance = nullptr;

} // namespace nkentseu

// ---------------------------------------------------------------------------
// Exports C (EMSCRIPTEN_KEEPALIVE) — appelés depuis le JS via Module._NkWASM*
// ---------------------------------------------------------------------------
#ifdef __EMSCRIPTEN__
extern "C" {
    EMSCRIPTEN_KEEPALIVE void _NkWASMFrame(int w,int h,int n)
    { nkentseu::NkWASMCameraBackend::_OnFrame(w,h,n); }

    EMSCRIPTEN_KEEPALIVE void _NkWASMStreamOK()
    { nkentseu::NkWASMCameraBackend::_OnStreamOK(); }

    EMSCRIPTEN_KEEPALIVE void _NkWASMStreamErr(const char* msg)
    { nkentseu::NkWASMCameraBackend::_OnStreamErr(msg); }

    EMSCRIPTEN_KEEPALIVE void _NkWASMDeviceList(const char* json)
    { nkentseu::NkWASMCameraBackend::_OnDeviceList(json); }
}
#endif
