#include <X11/Xlib.h>

int main() {
    Display* dpy = XOpenDisplay(nullptr);
    if (!dpy) return 1;

    int screen = DefaultScreen(dpy);
    Window win = XCreateSimpleWindow(dpy, RootWindow(dpy, screen),
        10, 10, 640, 480, 1,
        BlackPixel(dpy, screen), WhitePixel(dpy, screen));

    XSelectInput(dpy, win, ExposureMask | KeyPressMask | StructureNotifyMask);
    XMapWindow(dpy, win);

    bool running = true;
    while (running) {
        XEvent ev;
        XNextEvent(dpy, &ev);
        if (ev.type == KeyPress || ev.type == DestroyNotify) {
            running = false;
        }
    }

    XDestroyWindow(dpy, win);
    XCloseDisplay(dpy);
    return 0;
}
