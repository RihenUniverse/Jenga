# Android.mk - manual ndk-build sample for SDL3 + NativeActivity

LOCAL_PATH := $(call my-dir)

ifndef SDL3_ROOT
$(warning SDL3_ROOT is not set. Falling back to $(LOCAL_PATH)/third_party/SDL3)
SDL3_ROOT := $(LOCAL_PATH)/third_party/SDL3
endif

# Prebuilt SDL3 shared library
include $(CLEAR_VARS)
LOCAL_MODULE := SDL3
LOCAL_SRC_FILES := $(SDL3_ROOT)/lib/$(TARGET_ARCH_ABI)/libSDL3.so
LOCAL_EXPORT_C_INCLUDES := $(SDL3_ROOT)/include
include $(PREBUILT_SHARED_LIBRARY)

# NativeActivity shared library built by ndk-build
include $(CLEAR_VARS)
LOCAL_MODULE := SDL3NativeDemo
LOCAL_SRC_FILES := src/main.cpp
LOCAL_SHARED_LIBRARIES := SDL3
LOCAL_LDLIBS := -llog -landroid -lEGL -lGLESv2
LOCAL_CPPFLAGS += -std=c++17 -fexceptions -frtti
include $(BUILD_SHARED_LIBRARY)
