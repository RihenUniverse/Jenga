#import <Cocoa/Cocoa.h>

int main(int argc, const char** argv) {
    @autoreleasepool {
        [NSApplication sharedApplication];

        NSRect frame = NSMakeRect(0, 0, 800, 600);
        NSUInteger style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable;
        NSWindow* window = [[NSWindow alloc] initWithContentRect:frame
                                                        styleMask:style
                                                          backing:NSBackingStoreBuffered
                                                            defer:NO];
        [window setTitle:@"Jenga Cocoa"];
        [window makeKeyAndOrderFront:nil];
        [NSApp run];
    }
    return 0;
}
