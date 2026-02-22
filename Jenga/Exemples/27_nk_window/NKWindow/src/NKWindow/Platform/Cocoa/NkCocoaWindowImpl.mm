// =============================================================================
// NkCocoaWindowImpl.mm
// Implémentation macOS Cocoa de IWindowImpl.
// =============================================================================

#import <Cocoa/Cocoa.h>
#import <QuartzCore/CAMetalLayer.h>
#include "NkCocoaWindowImpl.h"
#import "../../Core/NkSystem.h"
#include <CoreGraphics/CoreGraphics.h>

// ---------------------------------------------------------------------------
// ObjC helpers — NSWindow + NSView délégués
// ---------------------------------------------------------------------------

@interface NkNSWindow : NSWindow
{
@public
    nkentseu::IWindowImpl* owner;
}
@end

@implementation NkNSWindow
- (BOOL)windowShouldClose:(id)sender { return YES; }
- (void)windowWillClose:(NSNotification*)n
{
    if (owner) {
        nkentseu::NkEvent ev(nkentseu::NkEventType::NK_CLOSE);
        owner->DispatchEvent(ev);
    }
}
@end

@interface NkNSView : NSView
{
@public
    nkentseu::IWindowImpl* owner;
}
@end

@implementation NkNSView
- (BOOL)wantsUpdateLayer { return YES; }
- (BOOL)acceptsFirstResponder { return YES; }
- (void)viewDidChangeBackingProperties
{
    [super viewDidChangeBackingProperties];
    if (owner) {
        float scale = (float)[[self window] backingScaleFactor];
        nkentseu::NkEvent ev(nkentseu::NkDpiData(scale));
        owner->DispatchEvent(ev);
    }
}
@end

// ---------------------------------------------------------------------------

namespace nkentseu
{

NkCocoaWindowImpl::NkCocoaWindowImpl()  = default;
NkCocoaWindowImpl::~NkCocoaWindowImpl() { if (mIsOpen) Close(); }

bool NkCocoaWindowImpl::Create(const NkWindowConfig& config, IEventImpl& /*eventImpl*/)
{
    mConfig  = config;
    mBgColor = config.bgColor;

    @autoreleasepool
    {
        // Style
        NSWindowStyleMask style = NSWindowStyleMaskBorderless;
        if (config.frame)
        {
            style  = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable;
            if (config.resizable)   style |= NSWindowStyleMaskResizable;
            if (config.minimizable) style |= NSWindowStyleMaskMiniaturizable;
        }

        NSRect frame = NSMakeRect(config.x, config.y, config.width, config.height);
        if (config.centered)
        {
            NSRect screen = [[NSScreen mainScreen] frame];
            frame.origin.x = (screen.size.width  - config.width)  / 2.0;
            frame.origin.y = (screen.size.height - config.height) / 2.0;
        }

        NkNSWindow* win = [[NkNSWindow alloc]
            initWithContentRect:frame
                      styleMask:style
                        backing:NSBackingStoreBuffered
                          defer:NO];
        win->owner = this;
        [win setTitle:[NSString stringWithUTF8String:config.title.c_str()]];
        [win setDelegate:(id<NSWindowDelegate>)win];
        [win setReleasedWhenClosed:NO];
        [win setAcceptsMouseMovedEvents:YES];

        NkNSView* view = [[NkNSView alloc] initWithFrame:frame];
        view->owner = this;
        [win setContentView:view];
        [win makeFirstResponder:view];

        // Metal layer
        CAMetalLayer* ml = [CAMetalLayer layer];
        ml.frame              = view.bounds;
        ml.autoresizingMask   = kCALayerWidthSizable | kCALayerHeightSizable;
        [view setLayer:ml];
        [view setWantsLayer:YES];

        if (config.visible)
        {
            [win makeKeyAndOrderFront:nil];
            [NSApp activateIgnoringOtherApps:YES];
        }

        mWindow     = win;
        mView       = view;
        mMetalLayer = ml;
        mIsOpen     = true;
    }
    return true;
}

void NkCocoaWindowImpl::Close()
{
    if (mWindow)
    {
        @autoreleasepool {
            [(NkNSWindow*)mWindow close];
            mWindow = nullptr;
            mView   = nullptr;
        }
    }
    mIsOpen = false;
}

bool NkCocoaWindowImpl::IsOpen() const { return mIsOpen; }

std::string NkCocoaWindowImpl::GetTitle() const
{
    if (!mWindow) return "";
    @autoreleasepool {
        return [[(NkNSWindow*)mWindow title] UTF8String];
    }
}

void NkCocoaWindowImpl::SetTitle(const std::string& title)
{
    mConfig.title = title;
    if (mWindow)
    {
        @autoreleasepool {
            [(NkNSWindow*)mWindow setTitle:
                [NSString stringWithUTF8String:title.c_str()]];
        }
    }
}

NkVec2u NkCocoaWindowImpl::GetSize() const
{
    if (!mWindow) return {};
    @autoreleasepool {
        NSRect r = [(NkNSWindow*)mWindow contentRectForFrameRect:
                    [(NkNSWindow*)mWindow frame]];
        return { static_cast<NkU32>(r.size.width),
                 static_cast<NkU32>(r.size.height) };
    }
}

NkVec2u NkCocoaWindowImpl::GetPosition() const
{
    if (!mWindow) return {};
    @autoreleasepool {
        NSRect r = [(NkNSWindow*)mWindow frame];
        return { static_cast<NkU32>(r.origin.x),
                 static_cast<NkU32>(r.origin.y) };
    }
}

float NkCocoaWindowImpl::GetDpiScale() const
{
    if (!mWindow) return 1.f;
    @autoreleasepool {
        return static_cast<float>([(NkNSWindow*)mWindow backingScaleFactor]);
    }
}

NkVec2u NkCocoaWindowImpl::GetDisplaySize() const
{
    @autoreleasepool {
        NSRect r = [[NSScreen mainScreen] frame];
        return { static_cast<NkU32>(r.size.width),
                 static_cast<NkU32>(r.size.height) };
    }
}

NkVec2u NkCocoaWindowImpl::GetDisplayPosition() const { return {}; }
NkError NkCocoaWindowImpl::GetLastError()        const { return mLastError; }

void NkCocoaWindowImpl::SetSize(NkU32 w, NkU32 h)
{
    if (mWindow)
    {
        @autoreleasepool {
            NSRect r = [(NkNSWindow*)mWindow frame];
            r.size.width  = w;
            r.size.height = h;
            [(NkNSWindow*)mWindow setFrame:r display:YES];
        }
    }
}

void NkCocoaWindowImpl::SetPosition(NkI32 x, NkI32 y)
{
    if (mWindow)
    {
        @autoreleasepool {
            [(NkNSWindow*)mWindow setFrameOrigin:NSMakePoint(x, y)];
        }
    }
}

void NkCocoaWindowImpl::SetVisible(bool v)
{
    if (mWindow)
    {
        @autoreleasepool {
            v ? [(NkNSWindow*)mWindow makeKeyAndOrderFront:nil]
              : [(NkNSWindow*)mWindow orderOut:nil];
        }
    }
}

void NkCocoaWindowImpl::Minimize()
{
    if (mWindow)
    {
        @autoreleasepool { [(NkNSWindow*)mWindow miniaturize:nil]; }
    }
}

void NkCocoaWindowImpl::Maximize()
{
    if (mWindow)
    {
        @autoreleasepool { [(NkNSWindow*)mWindow zoom:nil]; }
    }
}

void NkCocoaWindowImpl::Restore()
{
    if (mWindow)
    {
        @autoreleasepool { [(NkNSWindow*)mWindow deminiaturize:nil]; }
    }
}

void NkCocoaWindowImpl::SetFullscreen(bool fs)
{
    if (mWindow)
    {
        @autoreleasepool {
            BOOL isFs = ([(NkNSWindow*)mWindow styleMask] &
                         NSWindowStyleMaskFullScreen) != 0;
            if (fs != (bool)isFs)
                [(NkNSWindow*)mWindow toggleFullScreen:nil];
        }
    }
    mConfig.fullscreen = fs;
}

void NkCocoaWindowImpl::SetMousePosition(NkU32 x, NkU32 y)
{
    CGWarpMouseCursorPosition(CGPointMake(x, y));
}

void NkCocoaWindowImpl::ShowMouse(bool show)
{
    show ? [NSCursor unhide] : [NSCursor hide];
}

void NkCocoaWindowImpl::CaptureMouse(bool cap)
{
    cap ? CGAssociateMouseAndMouseCursorPosition(false)
        : CGAssociateMouseAndMouseCursorPosition(true);
}

void NkCocoaWindowImpl::SetBackgroundColor(NkU32 rgba) { mBgColor = rgba; }
NkU32 NkCocoaWindowImpl::GetBackgroundColor() const    { return mBgColor; }

NkSurfaceDesc NkCocoaWindowImpl::GetSurfaceDesc() const
{
    NkSurfaceDesc sd;
    auto sz       = GetSize();
    sd.width      = sz.x;
    sd.height     = sz.y;
    sd.dpi        = GetDpiScale();
    sd.view       = mView;
    sd.metalLayer = mMetalLayer;
    return sd;
}

void NkCocoaWindowImpl::BlitSoftwareFramebuffer(
    const NkU8* rgba8, NkU32 w, NkU32 h)
{
    if (!mMetalLayer || !rgba8) return;
    @autoreleasepool
    {
        CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
        CGDataProviderRef dp = CGDataProviderCreateWithData(
            nullptr, rgba8,
            static_cast<std::size_t>(w) * h * 4, nullptr);
        CGImageRef img = CGImageCreate(
            w, h, 8, 32, w * 4, cs,
            kCGBitmapByteOrder32Big | kCGImageAlphaPremultipliedLast,
            dp, nullptr, false, kCGRenderingIntentDefault);
        [(CAMetalLayer*)mMetalLayer setContents:(__bridge id)img];
        CGImageRelease(img);
        CGDataProviderRelease(dp);
        CGColorSpaceRelease(cs);
    }
}

void NkCocoaWindowImpl::SetEventCallback(NkEventCallback callback)
{
    mEventCallback = std::move(callback);
}

void NkCocoaWindowImpl::DispatchEvent(NkEvent& event)
{
    if (mEventCallback) mEventCallback(event);
}

} // namespace nkentseu
