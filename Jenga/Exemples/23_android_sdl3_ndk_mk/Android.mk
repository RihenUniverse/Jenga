# Android.mk - manual ndk-build sample for SDL3 + NativeActivity

LOCAL_PATH := $(call my-dir)

ifndef SDL3_ROOT
$(warning SDL3_ROOT is not set. Falling back to $(LOCAL_PATH)/externals/SDL3)
SDL3_ROOT := $(LOCAL_PATH)/externals/SDL3
endif

# Header layout support:
# 1) <SDL3_ROOT>/include/SDL3/SDL.h
# 2) <SDL3_ROOT>/prefab/modules/SDL3-Headers/include/SDL3/SDL.h (from .aar)
SDL3_INCLUDE_DIR := $(SDL3_ROOT)/include
ifeq ($(wildcard $(SDL3_INCLUDE_DIR)/SDL3/SDL.h),)
SDL3_INCLUDE_DIR := $(SDL3_ROOT)/prefab/modules/SDL3-Headers/include
endif

# Library layout support:
# 1) <SDL3_ROOT>/lib/<abi>/libSDL3.so
# 2) <SDL3_ROOT>/prefab/modules/SDL3-shared/libs/android.<abi>/libSDL3.so
SDL3_LIB_PATH := $(SDL3_ROOT)/lib/$(TARGET_ARCH_ABI)/libSDL3.so
ifeq ($(wildcard $(SDL3_LIB_PATH)),)
SDL3_LIB_PATH := $(SDL3_ROOT)/prefab/modules/SDL3-shared/libs/android.$(TARGET_ARCH_ABI)/libSDL3.so
endif

ifeq ($(wildcard $(SDL3_INCLUDE_DIR)/SDL3/SDL.h),)
$(error SDL3 headers not found. Check SDL3_ROOT=$(SDL3_ROOT))
endif

ifeq ($(wildcard $(SDL3_LIB_PATH)),)
$(error SDL3 lib not found for ABI $(TARGET_ARCH_ABI). Check SDL3_ROOT=$(SDL3_ROOT))
endif

# Prebuilt SDL3 shared library
include $(CLEAR_VARS)
LOCAL_MODULE := SDL3
LOCAL_SRC_FILES := $(SDL3_LIB_PATH)
LOCAL_EXPORT_C_INCLUDES := $(SDL3_INCLUDE_DIR)
include $(PREBUILT_SHARED_LIBRARY)

# NativeActivity shared library built by ndk-build
include $(CLEAR_VARS)
LOCAL_MODULE := main
LOCAL_SRC_FILES := \
    src/application.cpp \
    src/main_android.cpp
LOCAL_SHARED_LIBRARIES := SDL3
LOCAL_LDLIBS := -llog -landroid -lEGL -lGLESv2
LOCAL_CPPFLAGS += -std=c++17 -fexceptions -frtti
include $(BUILD_SHARED_LIBRARY)
