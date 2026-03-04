#include <emscripten.h>

EM_JS(void, clear_canvas, (), {
    const canvas = document.querySelector('canvas') || (() => {
        const c = document.createElement('canvas');
        c.width = 640;
        c.height = 480;
        document.body.appendChild(c);
        return c;
    })();
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#1b1f24';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#9dd3ff';
    ctx.fillRect(100, 100, 200, 120);
});

int main() {
    clear_canvas();
    return 0;
}
