#pragma once

#ifdef _WIN32
  #ifdef UWP_SHARED_MATH_EXPORTS
    #define UWP_SHARED_API __declspec(dllexport)
  #else
    #define UWP_SHARED_API __declspec(dllimport)
  #endif
#else
  #define UWP_SHARED_API
#endif

extern "C" UWP_SHARED_API int UwpSharedSub(int a, int b);
extern "C" UWP_SHARED_API int UwpSharedDiv2(int a);
