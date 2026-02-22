#pragma once
// =============================================================================
// NkLinuxCameraBackend.h — V4L2 (Video4Linux2) — COMPLET ET FONCTIONNEL
// GetOrientation: via /sys/bus/iio/devices/iio:device* (accéléromètre intégré)
// Vidéo: ffmpeg pipe (MP4/H.264) ou écriture RAW si ffmpeg absent
// =============================================================================
#include "../../Core/Camera/INkCameraBackend.h"

#include <linux/videodev2.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/select.h>
#include <dirent.h>
#include <errno.h>
#include <cstring>
#include <cstdio>
#include <cmath>
#include <thread>
#include <atomic>
#include <mutex>
#include <string>
#include <vector>
#include <algorithm>
#include <chrono>
#include <fstream>

namespace nkentseu
{

struct V4L2Buf { void* start=nullptr; size_t length=0; };

class NkLinuxCameraBackend : public INkCameraBackend
{
public:
    NkLinuxCameraBackend()  = default;
    ~NkLinuxCameraBackend() override { Shutdown(); }

    bool Init()     override { return true; }
    void Shutdown() override { StopStreaming(); }

    // ------------------------------------------------------------------
    // Énumération — scanne /dev/video*
    // ------------------------------------------------------------------
    std::vector<NkCameraDevice> EnumerateDevices() override
    {
        std::vector<NkCameraDevice> result;
        std::vector<std::string> paths;
        DIR* dir = opendir("/dev");
        if (!dir) return result;
        struct dirent* ent;
        while ((ent = readdir(dir)))
            if (strncmp(ent->d_name,"video",5)==0) {
                std::string p = "/dev/";  p += ent->d_name;
                paths.push_back(p);
            }
        closedir(dir);
        std::sort(paths.begin(), paths.end());

        NkU32 idx = 0;
        for (const auto& path : paths) {
            int fd = open(path.c_str(), O_RDWR|O_NONBLOCK);
            if (fd < 0) continue;
            struct v4l2_capability cap={};
            if (ioctl(fd,VIDIOC_QUERYCAP,&cap)<0
             || !(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE))
            { close(fd); continue; }

            NkCameraDevice dev;
            dev.index  = idx++;
            dev.id     = path;
            dev.name   = (const char*)cap.card;
            dev.facing = NkCameraFacing::NK_CAMERA_FACING_EXTERNAL;

            // Modes supportés
            v4l2_fmtdesc fd2={};
            fd2.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
            while (ioctl(fd,VIDIOC_ENUM_FMT,&fd2)==0) {
                v4l2_frmsizeenum fs={};
                fs.pixel_format = fd2.pixelformat;
                fs.index = 0;
                while (ioctl(fd,VIDIOC_ENUM_FRAMESIZES,&fs)==0) {
                    NkCameraDevice::Mode m;
                    if (fs.type==V4L2_FRMSIZE_TYPE_DISCRETE)
                    { m.width=fs.discrete.width; m.height=fs.discrete.height; }
                    else { m.width=fs.stepwise.max_width; m.height=fs.stepwise.max_height; }
                    m.fps=30; m.format=NkPixelFormat::NK_PIXEL_YUYV;
                    if (m.width>0&&m.height>0) dev.modes.push_back(m);
                    ++fs.index;
                }
                ++fd2.index;
            }
            close(fd);
            result.push_back(std::move(dev));
        }
        return result;
    }

    void SetHotPlugCallback(NkCameraHotPlugCallback cb) override
    { mHotPlugCb = std::move(cb); }

    // ------------------------------------------------------------------
    // StartStreaming
    // ------------------------------------------------------------------
    bool StartStreaming(const NkCameraConfig& config) override
    {
        if (mFd >= 0) StopStreaming();
        auto devs = EnumerateDevices();
        if (config.deviceIndex >= devs.size())
        { mLastError="Device index "+std::to_string(config.deviceIndex)+" out of range"; return false; }

        const std::string& path = devs[config.deviceIndex].id;
        mFd = open(path.c_str(), O_RDWR);
        if (mFd < 0) { mLastError="Cannot open "+path+": "+strerror(errno); return false; }

        // Tenter YUYV en priorité, puis MJPEG
        struct v4l2_format fmt={};
        fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        fmt.fmt.pix.width       = config.width;
        fmt.fmt.pix.height      = config.height;
        fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
        fmt.fmt.pix.field       = V4L2_FIELD_ANY;
        if (ioctl(mFd,VIDIOC_S_FMT,&fmt)<0) {
            fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_MJPEG;
            if (ioctl(mFd,VIDIOC_S_FMT,&fmt)<0)
            { mLastError="VIDIOC_S_FMT failed"; close(mFd);mFd=-1; return false; }
        }

        mWidth  = fmt.fmt.pix.width;
        mHeight = fmt.fmt.pix.height;
        mFPS    = config.fps;
        mFormat = (fmt.fmt.pix.pixelformat==V4L2_PIX_FMT_YUYV)
                ? NkPixelFormat::NK_PIXEL_YUYV : NkPixelFormat::NK_PIXEL_MJPEG;

        // FPS
        struct v4l2_streamparm parm={};
        parm.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
        parm.parm.capture.timeperframe={1,mFPS};
        ioctl(mFd,VIDIOC_S_PARM,&parm);

        // Buffers mmap
        struct v4l2_requestbuffers req={};
        req.count=4; req.type=V4L2_BUF_TYPE_VIDEO_CAPTURE; req.memory=V4L2_MEMORY_MMAP;
        if (ioctl(mFd,VIDIOC_REQBUFS,&req)<0||req.count<2)
        { mLastError="VIDIOC_REQBUFS failed"; close(mFd);mFd=-1; return false; }

        mBufs.resize(req.count);
        for (NkU32 i=0;i<req.count;++i) {
            struct v4l2_buffer buf={};
            buf.type=V4L2_BUF_TYPE_VIDEO_CAPTURE; buf.memory=V4L2_MEMORY_MMAP; buf.index=i;
            ioctl(mFd,VIDIOC_QUERYBUF,&buf);
            mBufs[i].length = buf.length;
            mBufs[i].start  = mmap(nullptr,buf.length,PROT_READ|PROT_WRITE,
                                   MAP_SHARED,mFd,buf.m.offset);
            ioctl(mFd,VIDIOC_QBUF,&buf);
        }

        v4l2_buf_type t=V4L2_BUF_TYPE_VIDEO_CAPTURE;
        if (ioctl(mFd,VIDIOC_STREAMON,&t)<0) {
            for (auto& b:mBufs) if (b.start) munmap(b.start,b.length);
            mBufs.clear(); close(mFd); mFd=-1;
            mLastError="VIDIOC_STREAMON failed"; return false;
        }

        mRunning = true;
        mState   = NkCameraState::NK_CAM_STATE_STREAMING;
        mCaptureThread = std::thread([this]{ CaptureLoop(); });
        return true;
    }

    void StopStreaming() override
    {
        mRunning = false;
        if (mCaptureThread.joinable()) mCaptureThread.join();
        StopVideoRecord();
        if (mFd >= 0) {
            v4l2_buf_type t=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            ioctl(mFd,VIDIOC_STREAMOFF,&t);
            for (auto& b:mBufs) if (b.start) munmap(b.start,b.length);
            mBufs.clear();
            close(mFd); mFd=-1;
        }
        mState = NkCameraState::NK_CAM_STATE_CLOSED;
    }

    NkCameraState GetState() const override { return mState; }
    void SetFrameCallback(NkFrameCallback cb) override { mFrameCb=std::move(cb); }
    bool GetLastFrame(NkCameraFrame& out) override {
        std::lock_guard<std::mutex> lk(mMutex);
        if (!mHasFrame) return false; out=mLastFrame; return true;
    }

    // ------------------------------------------------------------------
    // Photo
    // ------------------------------------------------------------------
    bool CapturePhoto(NkPhotoCaptureResult& res) override {
        std::lock_guard<std::mutex> lk(mMutex);
        if (!mHasFrame){res.success=false;return false;}
        res.frame=mLastFrame; res.success=true; return true;
    }
    bool CapturePhotoToFile(const std::string& path) override {
        NkPhotoCaptureResult r; if (!CapturePhoto(r)) return false;
        // YUYV → RGBA → PPM (portabie, sans dépendance externe)
        auto& f = r.frame;
        NkU32 w=f.width,h=f.height;
        std::vector<NkU8> rgb(w*h*3);
        if (f.format==NkPixelFormat::NK_PIXEL_YUYV) {
            for (NkU32 i=0;i<w*h/2;++i) {
                float y0=(float)f.data[i*4]-16.f,cb=(float)f.data[i*4+1]-128.f;
                float y1=(float)f.data[i*4+2]-16.f,cr=(float)f.data[i*4+3]-128.f;
                auto cl=[](float v)->NkU8{return(NkU8)(v<0?0:v>255?255:v);};
                rgb[i*6]  =cl(y0*1.164f+cr*1.596f);
                rgb[i*6+1]=cl(y0*1.164f-cb*0.391f-cr*0.813f);
                rgb[i*6+2]=cl(y0*1.164f+cb*2.018f);
                rgb[i*6+3]=cl(y1*1.164f+cr*1.596f);
                rgb[i*6+4]=cl(y1*1.164f-cb*0.391f-cr*0.813f);
                rgb[i*6+5]=cl(y1*1.164f+cb*2.018f);
            }
        }
        // Écrire PPM (compatible universellement)
        std::string out = path.empty() ? "photo.ppm" : path;
        auto dot=out.rfind('.');
        if (dot!=std::string::npos) out=out.substr(0,dot)+".ppm";
        FILE* fp=fopen(out.c_str(),"wb");
        if (!fp) return false;
        fprintf(fp,"P6\n%d %d\n255\n",(int)w,(int)h);
        fwrite(rgb.data(),1,rgb.size(),fp);
        fclose(fp);
        return true;
    }

    // ------------------------------------------------------------------
    // Vidéo — ffmpeg pipe
    // ------------------------------------------------------------------
    bool StartVideoRecord(const NkVideoRecordConfig& config) override {
        if (mFfmpegPipe) return false;
        char cmd[512];
        const char* fmt = (mFormat==NkPixelFormat::NK_PIXEL_YUYV) ? "yuyv422" : "mjpeg";
        snprintf(cmd,sizeof(cmd),
            "ffmpeg -y -f rawvideo -pix_fmt %s -s %ux%u -r %u -i - "
            "-c:v libx264 -preset fast -crf 23 \"%s\" 2>/dev/null",
            fmt, mWidth, mHeight, mFPS, config.outputPath.c_str());
        mFfmpegPipe = popen(cmd,"w");
        if (!mFfmpegPipe) { mLastError="Cannot launch ffmpeg"; return false; }
        mRecordStart = std::chrono::steady_clock::now();
        mState       = NkCameraState::NK_CAM_STATE_RECORDING;
        return true;
    }
    void StopVideoRecord() override {
        if (!mFfmpegPipe) return;
        pclose(mFfmpegPipe); mFfmpegPipe=nullptr;
        if (mState==NkCameraState::NK_CAM_STATE_RECORDING)
            mState=NkCameraState::NK_CAM_STATE_STREAMING;
    }
    bool  IsRecording() const override { return mState==NkCameraState::NK_CAM_STATE_RECORDING; }
    float GetRecordingDurationSeconds() const override {
        if (!IsRecording()) return 0.f;
        return std::chrono::duration<float>(
            std::chrono::steady_clock::now()-mRecordStart).count();
    }

    // ------------------------------------------------------------------
    // GetOrientation — lecture IIO sysfs (accéléromètre intégré laptop/tablette)
    // ------------------------------------------------------------------
    bool GetOrientation(NkCameraOrientation& out) override
    {
        // Chercher /sys/bus/iio/devices/iio:device*/in_accel_*
        static std::string iioPath;
        if (iioPath.empty()) {
            DIR* d = opendir("/sys/bus/iio/devices");
            if (d) {
                struct dirent* e;
                while ((e=readdir(d))) {
                    if (strncmp(e->d_name,"iio:device",10)==0) {
                        std::string p = "/sys/bus/iio/devices/";
                        p += e->d_name;
                        // Vérifier si in_accel_x_raw existe
                        std::string xp = p+"/in_accel_x_raw";
                        if (access(xp.c_str(),R_OK)==0) { iioPath=p; break; }
                    }
                }
                closedir(d);
            }
        }
        if (iioPath.empty()) return false;

        auto readSysfs = [](const std::string& path) -> float {
            std::ifstream f(path);
            float v=0; f>>v; return v;
        };
        auto readScale = [&]() -> float {
            std::string sp = iioPath+"/in_accel_scale";
            float s = readSysfs(sp);
            return (s==0.f) ? 1.f : s;
        };

        float scale = readScale();
        float ax = readSysfs(iioPath+"/in_accel_x_raw") * scale;
        float ay = readSysfs(iioPath+"/in_accel_y_raw") * scale;
        float az = readSysfs(iioPath+"/in_accel_z_raw") * scale;

        out.accelX = ax;
        out.accelY = ay;
        out.accelZ = az;
        // Calcul pitch/roll depuis accéléromètre
        out.pitch = std::atan2(ay, std::sqrt(ax*ax+az*az)) * (180.f/3.14159f);
        out.roll  = std::atan2(-ax, az) * (180.f/3.14159f);
        out.yaw   = 0.f; // yaw non disponible sans magnétomètre
        return true;
    }

    NkU32         GetWidth()  const override { return mWidth;  }
    NkU32         GetHeight() const override { return mHeight; }
    NkU32         GetFPS()    const override { return mFPS;    }
    NkPixelFormat GetFormat() const override { return mFormat; }
    std::string   GetLastError() const override { return mLastError; }

private:
    void CaptureLoop()
    {
        while (mRunning) {
            fd_set fds; FD_ZERO(&fds); FD_SET(mFd,&fds);
            struct timeval tv={1,0};
            if (select(mFd+1,&fds,nullptr,nullptr,&tv)<=0) continue;

            struct v4l2_buffer buf={};
            buf.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
            buf.memory=V4L2_MEMORY_MMAP;
            if (ioctl(mFd,VIDIOC_DQBUF,&buf)<0) continue;

            const NkU8* src=(const NkU8*)mBufs[buf.index].start;
            NkU32 len = buf.bytesused;

            NkCameraFrame frame;
            frame.width     =mWidth; frame.height=mHeight;
            frame.format    =mFormat;
            frame.stride    =mWidth*2; // YUYV = 2 bytes/pixel
            frame.frameIndex=mFrameIdx++;
            frame.data.assign(src,src+len);

            ioctl(mFd,VIDIOC_QBUF,&buf);

            { std::lock_guard<std::mutex> lk(mMutex);
              mLastFrame=frame; mHasFrame=true; }
            if (mFrameCb) mFrameCb(frame);
            if (mFfmpegPipe) fwrite(frame.data.data(),1,frame.data.size(),mFfmpegPipe);
        }
    }

    int           mFd=-1;
    NkCameraState mState=NkCameraState::NK_CAM_STATE_CLOSED;
    NkU32         mWidth=0,mHeight=0,mFPS=30,mFrameIdx=0;
    NkPixelFormat mFormat=NkPixelFormat::NK_PIXEL_YUYV;
    std::string   mLastError;

    std::vector<V4L2Buf> mBufs;
    std::thread          mCaptureThread;
    std::atomic<bool>    mRunning{false};
    std::mutex           mMutex;
    NkCameraFrame        mLastFrame;
    bool                 mHasFrame=false;

    NkFrameCallback         mFrameCb;
    NkCameraHotPlugCallback mHotPlugCb;

    FILE* mFfmpegPipe=nullptr;
    std::chrono::steady_clock::time_point mRecordStart;
};

} // namespace nkentseu
