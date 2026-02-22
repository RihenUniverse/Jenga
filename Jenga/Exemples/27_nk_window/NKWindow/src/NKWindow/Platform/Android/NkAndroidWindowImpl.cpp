// =============================================================================
// NkAndroidWindowImpl.cpp
// =============================================================================

#include "NkAndroidWindowImpl.h"
#include "NkAndroidEventImpl.h"
#include "../../Core/NkSystem.h"

#ifdef __ANDROID__
#include <android/window.h>
#include <jni.h>
#endif

namespace nkentseu
{

android_app* nk_android_global_app = nullptr;

bool NkAndroidWindowImpl::Create(const NkWindowConfig& config)
{
    mConfig = config;
#ifdef __ANDROID__
    if (!nk_android_global_app) { mLastError = NkError(1,"android_app null"); return false; }
    mNativeWindow = nk_android_global_app->window;
    if (!mNativeWindow) { mLastError = NkError(2,"ANativeWindow null"); return false; }

    ANativeWindow_acquire(mNativeWindow);
    UpdateSafeArea();

    IEventImpl* ev = NkGetEventImpl();
    if (ev) ev->Initialize(this, mNativeWindow);
    mIsOpen = true;
#endif
    return mIsOpen;
}

void NkAndroidWindowImpl::Close()
{
    IEventImpl* ev = NkGetEventImpl();
    if (ev) ev->Shutdown(mNativeWindow);
    if (mNativeWindow)
    {
#ifdef __ANDROID__
        ANativeWindow_release(mNativeWindow);
#endif
        mNativeWindow = nullptr;
    }
    mIsOpen = false;
}

NkVec2u NkAndroidWindowImpl::GetSize() const
{
#ifdef __ANDROID__
    if (!mNativeWindow) return {};
    return { static_cast<NkU32>(ANativeWindow_getWidth(mNativeWindow)),
             static_cast<NkU32>(ANativeWindow_getHeight(mNativeWindow)) };
#else
    return {};
#endif
}

float NkAndroidWindowImpl::GetDpiScale() const
{
#ifdef __ANDROID__
    if (!nk_android_global_app) return 1.f;
    AConfiguration* cfg = AConfiguration_new();
    AConfiguration_fromAssetManager(cfg, nk_android_global_app->activity->assetManager);
    int32_t dpi = AConfiguration_getDensity(cfg);
    AConfiguration_delete(cfg);
    return dpi / 160.f; // 160 dpi = mdpi = base scale 1.0
#else
    return 1.f;
#endif
}

NkSurfaceDesc NkAndroidWindowImpl::GetSurfaceDesc() const
{
    NkSurfaceDesc sd;
    auto sz = GetSize();
    sd.width  = sz.x;
    sd.height = sz.y;
    sd.dpi    = GetDpiScale();
#ifdef __ANDROID__
    sd.nativeWindow = mNativeWindow;
#endif
    return sd;
}

NkSafeAreaInsets NkAndroidWindowImpl::GetSafeAreaInsets() const
{
    return mSafeArea;
}

void NkAndroidWindowImpl::UpdateSafeArea()
{
#ifdef __ANDROID__
    // Android 9+ (API 28) : DisplayCutout via JNI
    if (!nk_android_global_app) return;
    JNIEnv* env = nullptr;
    nk_android_global_app->activity->vm->AttachCurrentThread(&env, nullptr);
    if (!env) return;

    jobject activity = nk_android_global_app->activity->clazz;

    // getWindow().getDecorView().getRootWindowInsets().getDisplayCutout()
    jclass actClass  = env->GetObjectClass(activity);
    jmethodID getWin = env->GetMethodID(actClass, "getWindow", "()Landroid/view/Window;");
    jobject win      = env->CallObjectMethod(activity, getWin);
    if (!win) goto done;

    {
        jclass winClass  = env->GetObjectClass(win);
        jmethodID getView= env->GetMethodID(winClass,"getDecorView","()Landroid/view/View;");
        jobject view     = env->CallObjectMethod(win, getView);
        if (!view) goto done;

        jclass viewClass = env->GetObjectClass(view);
        jmethodID getInsets = env->GetMethodID(viewClass,
            "getRootWindowInsets", "()Landroid/view/WindowInsets;");
        jobject insets   = env->CallObjectMethod(view, getInsets);
        if (!insets) goto done;

        // getSystemWindowInsetTop/Bottom/Left/Right (API 20+, safe fallback)
        jclass insClass  = env->GetObjectClass(insets);
        auto getInt = [&](const char* name) -> float
        {
            jmethodID m = env->GetMethodID(insClass, name, "()I");
            return m ? static_cast<float>(env->CallIntMethod(insets, m)) : 0.f;
        };
        mSafeArea.top    = getInt("getSystemWindowInsetTop");
        mSafeArea.bottom = getInt("getSystemWindowInsetBottom");
        mSafeArea.left   = getInt("getSystemWindowInsetLeft");
        mSafeArea.right  = getInt("getSystemWindowInsetRight");
    }
done:
    nk_android_global_app->activity->vm->DetachCurrentThread();
#endif
}

} // namespace nkentseu
