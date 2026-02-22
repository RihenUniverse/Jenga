#pragma once

// =============================================================================
// NkAndroid.h
// Point d'entrée Android NDK.
// =============================================================================

#include "../Core/NkEntry.h"
// #include "../Platform/Android/NkAndroidWindowImpl.h"
#include <android_native_app_glue.h>
#include <jni.h>
#include <string>
#include <vector>

#ifndef NK_APP_NAME
#define NK_APP_NAME "android_app"
#endif

namespace nkentseu { NkEntryState* gState = nullptr; }

void android_main(android_app* app)
{
    nk_android_global_app = app;

    // Récupérer les infos via JNI
    JNIEnv* env = nullptr;
    app->activity->vm->AttachCurrentThread(&env, nullptr);

    std::string packageName, versionName, internalPath, externalPath;
    internalPath  = app->activity->internalDataPath  ? app->activity->internalDataPath  : "";
    externalPath  = app->activity->externalDataPath  ? app->activity->externalDataPath  : "";

    if (env)
    {
        jobject actObj  = app->activity->clazz;
        jclass  actCls  = env->GetObjectClass(actObj);
        jmethodID getPkg = env->GetMethodID(actCls, "getPackageName",
                                            "()Ljava/lang/String;");
        if (getPkg)
        {
            auto jstr = static_cast<jstring>(env->CallObjectMethod(actObj, getPkg));
            if (jstr)
            {
                const char* cs = env->GetStringUTFChars(jstr, nullptr);
                if (cs) { packageName = cs; env->ReleaseStringUTFChars(jstr, cs); }
                env->DeleteLocalRef(jstr);
            }
        }
        app->activity->vm->DetachCurrentThread();
    }

    std::vector<std::string> args = { packageName };

    nkentseu::NkEntryState state(app, args);
    state.appName = NK_APP_NAME;
    nkentseu::gState = &state;

    nkmain(state);

    nkentseu::gState       = nullptr;
    nk_android_global_app = nullptr;
}
