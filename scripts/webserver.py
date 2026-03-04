#!/usr/bin/env python3
"""
Simple HTTP server for testing Emscripten builds locally.
Resolves CORS issues with file:// protocol.

Usage:
    python webserver.py [port] [directory]

Examples:
    python webserver.py
    python webserver.py 8080
    python webserver.py 8080 ./Build/Bin/Debug
"""

import http.server
import socketserver
import sys
import os
from pathlib import Path

def main():
    # Configuration
    port = 8000
    directory = "."

    # Parse arguments
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)

    if len(sys.argv) > 2:
        directory = sys.argv[2]
        if not os.path.exists(directory):
            print(f"Directory does not exist: {directory}")
            sys.exit(1)

    # Change to target directory
    os.chdir(directory)

    # Create server with proper MIME types
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        extensions_map = {
            '': 'application/octet-stream',
            '.manifest': 'text/cache-manifest',
            '.html': 'text/html',
            '.png': 'image/png',
            '.jpg': 'image/jpg',
            '.svg': 'image/svg+xml',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.wasm': 'application/wasm',
            '.json': 'application/json',
            '.xml': 'application/xml',
        }

        def end_headers(self):
            # Add CORS headers for local development
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
            self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
            super().end_headers()

    # Start server
    Handler = MyHTTPRequestHandler

    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("=" * 60)
        print(f"🌐 Emscripten Web Server Running")
        print("=" * 60)
        print(f"📁 Serving directory: {Path(directory).absolute()}")
        print(f"🔗 Local URL: http://localhost:{port}")
        print(f"🔗 Network URL: http://127.0.0.1:{port}")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        print("=" * 60)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped")
            sys.exit(0)

if __name__ == "__main__":
    main()
