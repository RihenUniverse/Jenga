/**
 * Jenga Example 25 — OpenGL Colored Triangle
 *
 * Renders a triangle with per-vertex colors (red, green, blue) and hardware
 * interpolation using OpenGL ES 2.0 compatible shaders.
 *
 * Each platform uses its native windowing system:
 *   Windows  — Win32 + WGL  + OpenGL 2.0+
 *   Android  — NativeActivity + EGL + GLES 3.0
 *   Web      — Emscripten + GLES 2.0 (WebGL)
 *   Linux    — X11 + GLX + OpenGL 2.0+
 */

// ════════════════════════════════════════════════════════════════════════════
// Shared shader sources & vertex data
// ════════════════════════════════════════════════════════════════════════════

static const char* kVertexShader =
    "attribute vec2 aPos;\n"
    "attribute vec3 aColor;\n"
    "varying vec3 vColor;\n"
    "void main() {\n"
    "    gl_Position = vec4(aPos, 0.0, 1.0);\n"
    "    vColor = aColor;\n"
    "}\n";

static const char* kFragmentShader =
    "#ifdef GL_ES\n"
    "precision mediump float;\n"
    "#endif\n"
    "varying vec3 vColor;\n"
    "void main() {\n"
    "    gl_FragColor = vec4(vColor, 1.0);\n"
    "}\n";

// x, y,   r, g, b
static const float kTriangle[] = {
     0.0f,  0.6f,   1.0f, 0.0f, 0.0f,   // top — red
    -0.6f, -0.4f,   0.0f, 1.0f, 0.0f,   // bottom-left — green
     0.6f, -0.4f,   0.0f, 0.0f, 1.0f,   // bottom-right — blue
};

// ════════════════════════════════════════════════════════════════════════════
//  ANDROID — NativeActivity + EGL + GLES3
// ════════════════════════════════════════════════════════════════════════════
#if defined(__ANDROID__)

#include <android/log.h>
#include <android_native_app_glue.h>
#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <cstdlib>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  "GLTriangle", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "GLTriangle", __VA_ARGS__)

static GLuint compileShader(GLenum type, const char* src) {
    GLuint s = glCreateShader(type);
    glShaderSource(s, 1, &src, nullptr);
    glCompileShader(s);
    GLint ok = 0; glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) { char buf[512]; glGetShaderInfoLog(s, 512, nullptr, buf); LOGE("Shader: %s", buf); }
    return s;
}

static GLuint createProgram() {
    GLuint vs = compileShader(GL_VERTEX_SHADER,   kVertexShader);
    GLuint fs = compileShader(GL_FRAGMENT_SHADER, kFragmentShader);
    GLuint p  = glCreateProgram();
    glAttachShader(p, vs); glAttachShader(p, fs);
    glLinkProgram(p);
    glDeleteShader(vs); glDeleteShader(fs);
    return p;
}

void android_main(struct android_app* app) {
    // Wait for window
    int events; struct android_poll_source* source;
    while (!app->window) {
        while (ALooper_pollOnce(0, nullptr, &events, (void**)&source) >= 0)
            if (source) source->process(app, source);
    }

    // EGL init
    EGLDisplay dpy = eglGetDisplay(EGL_DEFAULT_DISPLAY);
    eglInitialize(dpy, nullptr, nullptr);
    const EGLint attribs[] = { EGL_RENDERABLE_TYPE, EGL_OPENGL_ES3_BIT, EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
                                EGL_BLUE_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_RED_SIZE, 8, EGL_NONE };
    EGLConfig cfg; EGLint numCfg;
    eglChooseConfig(dpy, attribs, &cfg, 1, &numCfg);
    EGLSurface sfc = eglCreateWindowSurface(dpy, cfg, app->window, nullptr);
    const EGLint ctxAttribs[] = { EGL_CONTEXT_CLIENT_VERSION, 3, EGL_NONE };
    EGLContext ctx = eglCreateContext(dpy, cfg, EGL_NO_CONTEXT, ctxAttribs);
    eglMakeCurrent(dpy, sfc, sfc, ctx);

    // Setup GL
    GLuint prog = createProgram();
    glUseProgram(prog);
    GLint aPos   = glGetAttribLocation(prog, "aPos");
    GLint aColor = glGetAttribLocation(prog, "aColor");

    LOGI("OpenGL ES triangle running");

    // Render loop
    while (!app->destroyRequested) {
        while (ALooper_pollOnce(0, nullptr, &events, (void**)&source) >= 0) {
            if (source) source->process(app, source);
            if (app->destroyRequested) break;
        }
        if (app->destroyRequested) break;

        EGLint w, h;
        eglQuerySurface(dpy, sfc, EGL_WIDTH,  &w);
        eglQuerySurface(dpy, sfc, EGL_HEIGHT, &h);
        glViewport(0, 0, w, h);
        glClearColor(0.1f, 0.1f, 0.12f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        glVertexAttribPointer(aPos,   2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle);
        glEnableVertexAttribArray(aPos);
        glVertexAttribPointer(aColor, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle + 2);
        glEnableVertexAttribArray(aColor);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        eglSwapBuffers(dpy, sfc);
    }

    eglMakeCurrent(dpy, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
    eglDestroyContext(dpy, ctx);
    eglDestroySurface(dpy, sfc);
    eglTerminate(dpy);
}

// ════════════════════════════════════════════════════════════════════════════
//  WEB — Emscripten + GLES2 (WebGL)
// ════════════════════════════════════════════════════════════════════════════
#elif defined(__EMSCRIPTEN__)

#include <emscripten.h>
#include <emscripten/html5.h>
#include <GLES2/gl2.h>
#include <cstdio>

static GLuint g_prog = 0;
static GLint  g_aPos = -1, g_aColor = -1;

static GLuint compileShader(GLenum type, const char* src) {
    GLuint s = glCreateShader(type);
    glShaderSource(s, 1, &src, nullptr);
    glCompileShader(s);
    GLint ok = 0; glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) { char buf[512]; glGetShaderInfoLog(s, 512, nullptr, buf); std::printf("Shader: %s\n", buf); }
    return s;
}

static GLuint createProgram() {
    GLuint vs = compileShader(GL_VERTEX_SHADER,   kVertexShader);
    GLuint fs = compileShader(GL_FRAGMENT_SHADER, kFragmentShader);
    GLuint p  = glCreateProgram();
    glAttachShader(p, vs); glAttachShader(p, fs);
    glLinkProgram(p);
    glDeleteShader(vs); glDeleteShader(fs);
    return p;
}

static void mainLoop() {
    int w, h;
    emscripten_get_canvas_element_size("#canvas", &w, &h);
    glViewport(0, 0, w, h);
    glClearColor(0.1f, 0.1f, 0.12f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    glUseProgram(g_prog);
    glVertexAttribPointer(g_aPos,   2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle);
    glEnableVertexAttribArray(g_aPos);
    glVertexAttribPointer(g_aColor, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle + 2);
    glEnableVertexAttribArray(g_aColor);
    glDrawArrays(GL_TRIANGLES, 0, 3);
}

int main() {
    EmscriptenWebGLContextAttributes attr;
    emscripten_webgl_init_context_attributes(&attr);
    attr.majorVersion = 1;
    EMSCRIPTEN_WEBGL_CONTEXT_HANDLE ctx = emscripten_webgl_create_context("#canvas", &attr);
    emscripten_webgl_make_context_current(ctx);

    g_prog   = createProgram();
    g_aPos   = glGetAttribLocation(g_prog, "aPos");
    g_aColor = glGetAttribLocation(g_prog, "aColor");

    std::printf("WebGL triangle running\n");
    emscripten_set_main_loop(mainLoop, 0, 1);
    return 0;
}

// ════════════════════════════════════════════════════════════════════════════
//  WINDOWS — Win32 + WGL + OpenGL 2.0+
// ════════════════════════════════════════════════════════════════════════════
#elif defined(_WIN32)

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <GL/gl.h>
#include <cstdio>

// GL 2.0 types & constants not in MinGW gl.h
typedef char GLchar;
#ifndef GL_FRAGMENT_SHADER
#define GL_FRAGMENT_SHADER  0x8B30
#define GL_VERTEX_SHADER    0x8B31
#define GL_COMPILE_STATUS   0x8B81
#define GL_LINK_STATUS      0x8B82
#define GL_INFO_LOG_LENGTH  0x8B84
#endif

// GL 2.0 function pointers
typedef GLuint (APIENTRY *PFNGLCREATESHADERPROC)(GLenum);
typedef void   (APIENTRY *PFNGLSHADERSOURCEPROC)(GLuint, GLsizei, const GLchar**, const GLint*);
typedef void   (APIENTRY *PFNGLCOMPILESHADERPROC)(GLuint);
typedef void   (APIENTRY *PFNGLGETSHADERIVPROC)(GLuint, GLenum, GLint*);
typedef void   (APIENTRY *PFNGLGETSHADERINFOLOGPROC)(GLuint, GLsizei, GLsizei*, GLchar*);
typedef GLuint (APIENTRY *PFNGLCREATEPROGRAMPROC)();
typedef void   (APIENTRY *PFNGLATTACHSHADERPROC)(GLuint, GLuint);
typedef void   (APIENTRY *PFNGLLINKPROGRAMPROC)(GLuint);
typedef void   (APIENTRY *PFNGLUSEPROGRAMPROC)(GLuint);
typedef GLint  (APIENTRY *PFNGLGETATTRIBLOCATIONPROC)(GLuint, const GLchar*);
typedef void   (APIENTRY *PFNGLENABLEVERTEXATTRIBARRAYPROC)(GLuint);
typedef void   (APIENTRY *PFNGLVERTEXATTRIBPOINTERPROC)(GLuint, GLint, GLenum, GLboolean, GLsizei, const void*);
typedef void   (APIENTRY *PFNGLDELETESHADERPROC)(GLuint);
typedef void   (APIENTRY *PFNGLDELETEPROGRAMPROC)(GLuint);

static PFNGLCREATESHADERPROC            pglCreateShader;
static PFNGLSHADERSOURCEPROC            pglShaderSource;
static PFNGLCOMPILESHADERPROC           pglCompileShader;
static PFNGLGETSHADERIVPROC             pglGetShaderiv;
static PFNGLGETSHADERINFOLOGPROC        pglGetShaderInfoLog;
static PFNGLCREATEPROGRAMPROC           pglCreateProgram;
static PFNGLATTACHSHADERPROC            pglAttachShader;
static PFNGLLINKPROGRAMPROC             pglLinkProgram;
static PFNGLUSEPROGRAMPROC              pglUseProgram;
static PFNGLGETATTRIBLOCATIONPROC       pglGetAttribLocation;
static PFNGLENABLEVERTEXATTRIBARRAYPROC pglEnableVertexAttribArray;
static PFNGLVERTEXATTRIBPOINTERPROC     pglVertexAttribPointer;
static PFNGLDELETESHADERPROC            pglDeleteShader;
static PFNGLDELETEPROGRAMPROC           pglDeleteProgram;

static bool loadGL() {
    #define LOAD(name, type) p##name = (type)wglGetProcAddress(#name); if (!p##name) return false
    LOAD(glCreateShader,            PFNGLCREATESHADERPROC);
    LOAD(glShaderSource,            PFNGLSHADERSOURCEPROC);
    LOAD(glCompileShader,           PFNGLCOMPILESHADERPROC);
    LOAD(glGetShaderiv,             PFNGLGETSHADERIVPROC);
    LOAD(glGetShaderInfoLog,        PFNGLGETSHADERINFOLOGPROC);
    LOAD(glCreateProgram,           PFNGLCREATEPROGRAMPROC);
    LOAD(glAttachShader,            PFNGLATTACHSHADERPROC);
    LOAD(glLinkProgram,             PFNGLLINKPROGRAMPROC);
    LOAD(glUseProgram,              PFNGLUSEPROGRAMPROC);
    LOAD(glGetAttribLocation,       PFNGLGETATTRIBLOCATIONPROC);
    LOAD(glEnableVertexAttribArray, PFNGLENABLEVERTEXATTRIBARRAYPROC);
    LOAD(glVertexAttribPointer,     PFNGLVERTEXATTRIBPOINTERPROC);
    LOAD(glDeleteShader,            PFNGLDELETESHADERPROC);
    LOAD(glDeleteProgram,           PFNGLDELETEPROGRAMPROC);
    #undef LOAD
    return true;
}

static GLuint compileShader(GLenum type, const char* src) {
    GLuint s = pglCreateShader(type);
    pglShaderSource(s, 1, &src, nullptr);
    pglCompileShader(s);
    GLint ok = 0; pglGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) { char buf[512]; pglGetShaderInfoLog(s, 512, nullptr, buf); std::printf("Shader: %s\n", buf); }
    return s;
}

static GLuint createProgram() {
    GLuint vs = compileShader(GL_VERTEX_SHADER,   kVertexShader);
    GLuint fs = compileShader(GL_FRAGMENT_SHADER, kFragmentShader);
    GLuint p  = pglCreateProgram();
    pglAttachShader(p, vs); pglAttachShader(p, fs);
    pglLinkProgram(p);
    pglDeleteShader(vs); pglDeleteShader(fs);
    return p;
}

static GLuint g_prog = 0;
static GLint  g_aPos = -1, g_aColor = -1;
static HDC    g_hdc  = nullptr;

static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
    case WM_SIZE:
        glViewport(0, 0, LOWORD(lp), HIWORD(lp));
        return 0;
    case WM_CLOSE:
        PostQuitMessage(0);
        return 0;
    case WM_KEYDOWN:
        if (wp == VK_ESCAPE) PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcA(hwnd, msg, wp, lp);
}

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE, LPSTR, int) {
    WNDCLASSA wc{};
    wc.style         = CS_OWNDC;
    wc.lpfnWndProc   = WndProc;
    wc.hInstance      = hInst;
    wc.hCursor        = LoadCursor(nullptr, IDC_ARROW);
    wc.lpszClassName  = "GLTriangle";
    RegisterClassA(&wc);

    HWND hwnd = CreateWindowA("GLTriangle", "Jenga — OpenGL Triangle",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE, CW_USEDEFAULT, CW_USEDEFAULT, 800, 600,
        nullptr, nullptr, hInst, nullptr);

    g_hdc = GetDC(hwnd);
    PIXELFORMATDESCRIPTOR pfd{};
    pfd.nSize        = sizeof(pfd);
    pfd.nVersion     = 1;
    pfd.dwFlags      = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
    pfd.iPixelType   = PFD_TYPE_RGBA;
    pfd.cColorBits   = 32;
    pfd.cDepthBits   = 24;
    SetPixelFormat(g_hdc, ChoosePixelFormat(g_hdc, &pfd), &pfd);

    HGLRC hrc = wglCreateContext(g_hdc);
    wglMakeCurrent(g_hdc, hrc);

    if (!loadGL()) {
        MessageBoxA(hwnd, "Failed to load OpenGL 2.0 functions", "Error", MB_OK);
        return 1;
    }

    g_prog   = createProgram();
    g_aPos   = pglGetAttribLocation(g_prog, "aPos");
    g_aColor = pglGetAttribLocation(g_prog, "aColor");

    MSG msg{};
    bool running = true;
    while (running) {
        while (PeekMessageA(&msg, nullptr, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) { running = false; break; }
            TranslateMessage(&msg);
            DispatchMessageA(&msg);
        }

        glClearColor(0.1f, 0.1f, 0.12f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        pglUseProgram(g_prog);
        pglVertexAttribPointer(g_aPos,   2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle);
        pglEnableVertexAttribArray(g_aPos);
        pglVertexAttribPointer(g_aColor, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle + 2);
        pglEnableVertexAttribArray(g_aColor);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        SwapBuffers(g_hdc);
    }

    pglDeleteProgram(g_prog);
    wglMakeCurrent(nullptr, nullptr);
    wglDeleteContext(hrc);
    ReleaseDC(hwnd, g_hdc);
    DestroyWindow(hwnd);
    return 0;
}

// ════════════════════════════════════════════════════════════════════════════
//  LINUX — X11 + GLX + OpenGL 2.0+
// ════════════════════════════════════════════════════════════════════════════
#elif defined(__linux__)

#include <X11/Xlib.h>
#include <GL/glx.h>
#include <GL/gl.h>
#include <cstdio>
#include <cstdlib>

// GL 2.0 types & constants
typedef char GLchar;
#ifndef GL_FRAGMENT_SHADER
#define GL_FRAGMENT_SHADER  0x8B30
#define GL_VERTEX_SHADER    0x8B31
#define GL_COMPILE_STATUS   0x8B81
#endif

typedef GLuint (*PFNGLCREATESHADERPROC)(GLenum);
typedef void   (*PFNGLSHADERSOURCEPROC)(GLuint, GLsizei, const GLchar**, const GLint*);
typedef void   (*PFNGLCOMPILESHADERPROC)(GLuint);
typedef void   (*PFNGLGETSHADERIVPROC)(GLuint, GLenum, GLint*);
typedef void   (*PFNGLGETSHADERINFOLOGPROC)(GLuint, GLsizei, GLsizei*, GLchar*);
typedef GLuint (*PFNGLCREATEPROGRAMPROC)();
typedef void   (*PFNGLATTACHSHADERPROC)(GLuint, GLuint);
typedef void   (*PFNGLLINKPROGRAMPROC)(GLuint);
typedef void   (*PFNGLUSEPROGRAMPROC)(GLuint);
typedef GLint  (*PFNGLGETATTRIBLOCATIONPROC)(GLuint, const GLchar*);
typedef void   (*PFNGLENABLEVERTEXATTRIBARRAYPROC)(GLuint);
typedef void   (*PFNGLVERTEXATTRIBPOINTERPROC)(GLuint, GLint, GLenum, GLboolean, GLsizei, const void*);
typedef void   (*PFNGLDELETESHADERPROC)(GLuint);
typedef void   (*PFNGLDELETEPROGRAMPROC)(GLuint);

static PFNGLCREATESHADERPROC            pglCreateShader;
static PFNGLSHADERSOURCEPROC            pglShaderSource;
static PFNGLCOMPILESHADERPROC           pglCompileShader;
static PFNGLGETSHADERIVPROC             pglGetShaderiv;
static PFNGLGETSHADERINFOLOGPROC        pglGetShaderInfoLog;
static PFNGLCREATEPROGRAMPROC           pglCreateProgram;
static PFNGLATTACHSHADERPROC            pglAttachShader;
static PFNGLLINKPROGRAMPROC             pglLinkProgram;
static PFNGLUSEPROGRAMPROC              pglUseProgram;
static PFNGLGETATTRIBLOCATIONPROC       pglGetAttribLocation;
static PFNGLENABLEVERTEXATTRIBARRAYPROC pglEnableVertexAttribArray;
static PFNGLVERTEXATTRIBPOINTERPROC     pglVertexAttribPointer;
static PFNGLDELETESHADERPROC            pglDeleteShader;
static PFNGLDELETEPROGRAMPROC           pglDeleteProgram;

static bool loadGL() {
    #define LOAD(name, type) p##name = (type)glXGetProcAddress((const GLubyte*)#name); if (!p##name) return false
    LOAD(glCreateShader,            PFNGLCREATESHADERPROC);
    LOAD(glShaderSource,            PFNGLSHADERSOURCEPROC);
    LOAD(glCompileShader,           PFNGLCOMPILESHADERPROC);
    LOAD(glGetShaderiv,             PFNGLGETSHADERIVPROC);
    LOAD(glGetShaderInfoLog,        PFNGLGETSHADERINFOLOGPROC);
    LOAD(glCreateProgram,           PFNGLCREATEPROGRAMPROC);
    LOAD(glAttachShader,            PFNGLATTACHSHADERPROC);
    LOAD(glLinkProgram,             PFNGLLINKPROGRAMPROC);
    LOAD(glUseProgram,              PFNGLUSEPROGRAMPROC);
    LOAD(glGetAttribLocation,       PFNGLGETATTRIBLOCATIONPROC);
    LOAD(glEnableVertexAttribArray, PFNGLENABLEVERTEXATTRIBARRAYPROC);
    LOAD(glVertexAttribPointer,     PFNGLVERTEXATTRIBPOINTERPROC);
    LOAD(glDeleteShader,            PFNGLDELETESHADERPROC);
    LOAD(glDeleteProgram,           PFNGLDELETEPROGRAMPROC);
    #undef LOAD
    return true;
}

static GLuint compileShader(GLenum type, const char* src) {
    GLuint s = pglCreateShader(type);
    pglShaderSource(s, 1, &src, nullptr);
    pglCompileShader(s);
    GLint ok = 0; pglGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) { char buf[512]; pglGetShaderInfoLog(s, 512, nullptr, buf); std::printf("Shader: %s\n", buf); }
    return s;
}

static GLuint createProgram() {
    GLuint vs = compileShader(GL_VERTEX_SHADER,   kVertexShader);
    GLuint fs = compileShader(GL_FRAGMENT_SHADER, kFragmentShader);
    GLuint p  = pglCreateProgram();
    pglAttachShader(p, vs); pglAttachShader(p, fs);
    pglLinkProgram(p);
    pglDeleteShader(vs); pglDeleteShader(fs);
    return p;
}

int main() {
    Display* dpy = XOpenDisplay(nullptr);
    if (!dpy) { std::printf("Cannot open X display\n"); return 1; }

    int screen = DefaultScreen(dpy);
    int glxAttribs[] = { GLX_RGBA, GLX_DOUBLEBUFFER, GLX_DEPTH_SIZE, 24, None };
    XVisualInfo* vi = glXChooseVisual(dpy, screen, glxAttribs);
    if (!vi) { std::printf("No suitable GLX visual\n"); return 1; }

    Colormap cmap = XCreateColormap(dpy, RootWindow(dpy, screen), vi->visual, AllocNone);
    XSetWindowAttributes swa{};
    swa.colormap   = cmap;
    swa.event_mask = ExposureMask | KeyPressMask | StructureNotifyMask;
    Window win = XCreateWindow(dpy, RootWindow(dpy, screen), 0, 0, 800, 600, 0,
        vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);
    XStoreName(dpy, win, "Jenga — OpenGL Triangle");
    XMapWindow(dpy, win);

    GLXContext glc = glXCreateContext(dpy, vi, nullptr, GL_TRUE);
    glXMakeCurrent(dpy, win, glc);
    XFree(vi);

    if (!loadGL()) { std::printf("Failed to load GL 2.0 functions\n"); return 1; }

    GLuint prog   = createProgram();
    GLint  aPos   = pglGetAttribLocation(prog, "aPos");
    GLint  aColor = pglGetAttribLocation(prog, "aColor");

    std::printf("OpenGL triangle running on Linux\n");

    int width = 800, height = 600;
    bool running = true;
    while (running) {
        while (XPending(dpy)) {
            XEvent ev;
            XNextEvent(dpy, &ev);
            if (ev.type == KeyPress) running = false;
            if (ev.type == ConfigureNotify) {
                width  = ev.xconfigure.width;
                height = ev.xconfigure.height;
            }
        }

        glViewport(0, 0, width, height);
        glClearColor(0.1f, 0.1f, 0.12f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        pglUseProgram(prog);
        pglVertexAttribPointer(aPos,   2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle);
        pglEnableVertexAttribArray(aPos);
        pglVertexAttribPointer(aColor, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), kTriangle + 2);
        pglEnableVertexAttribArray(aColor);
        glDrawArrays(GL_TRIANGLES, 0, 3);

        glXSwapBuffers(dpy, win);
    }

    pglDeleteProgram(prog);
    glXMakeCurrent(dpy, None, nullptr);
    glXDestroyContext(dpy, glc);
    XDestroyWindow(dpy, win);
    XCloseDisplay(dpy);
    return 0;
}

// ════════════════════════════════════════════════════════════════════════════
//  FALLBACK
// ════════════════════════════════════════════════════════════════════════════
#else

#include <cstdio>
int main() {
    std::printf("OpenGL triangle example — unsupported platform.\n");
    return 0;
}

#endif
