#pragma once
#if defined(_WIN32)
#  ifdef GREETER_BUILD
#    define GREETER_API __declspec(dllexport)
#  else
#    define GREETER_API __declspec(dllimport)
#  endif
#else
#  define GREETER_API
#endif
extern "C" GREETER_API const char* greet();
