"""
Watch command - Auto-rebuild on file changes
"""

def execute(args):
    """Watch files and auto-rebuild"""
    import time
    import os
    from pathlib import Path
    from Jenga.Commands.build import execute as build
    
    print("👀 Watching for changes... (Ctrl+C to stop)")
    
    # Trouver les fichiers à surveiller
    watch_patterns = ["*.cpp", "*.h", "*.c", "*.hpp", "*.jenga"]
    last_mtime = {}
    
    def get_files():
        files = []
        for pattern in watch_patterns:
            files.extend(Path(".").rglob(pattern))
        return files
    
    # Initial build
    print("\n🔨 Initial build...")
    build([])
    
    try:
        while True:
            changed = False
            for file in get_files():
                mtime = file.stat().st_mtime
                if file not in last_mtime or last_mtime[file] != mtime:
                    if file in last_mtime:  # Pas au premier tour
                        print(f"\n📝 Changed: {file}")
                        changed = True
                    last_mtime[file] = mtime
            
            if changed:
                print("\n🔨 Rebuilding...")
                build([])
                print("\n✅ Build complete. Watching...")
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching")
        return 0