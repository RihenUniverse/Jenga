#pragma once

#ifdef _WIN32
  #ifdef XBOX_SHARED_MATH_EXPORTS
    #define XBOX_SHARED_API __declspec(dllexport)
  #else
    #define XBOX_SHARED_API __declspec(dllimport)
  #endif
#else
  #define XBOX_SHARED_API
#endif

extern "C" XBOX_SHARED_API int XboxSharedSub(int a, int b);
extern "C" XBOX_SHARED_API int XboxSharedDiv2(int a);
