#!/usr/bin/env python3
"""
Serveur HTTP local pour tester les applications Emscripten
Usage: python run_web_server.py
"""
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Configuration
PORT = 8080
BUILD_DIR = Path(__file__).parent / "Build" / "Bin" / "Debug-Web" / "GLTriangle"

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP avec headers CORS pour WebAssembly"""

    def end_headers(self):
        # Ajouter headers CORS pour permettre le chargement .wasm
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        # MIME types corrects pour Emscripten
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def guess_type(self, path):
        """Override pour ajouter le type MIME .wasm"""
        mimetype = super().guess_type(path)
        if path.endswith('.wasm'):
            return 'application/wasm'
        return mimetype

if __name__ == '__main__':
    # Changer vers le répertoire de build
    if BUILD_DIR.exists():
        import os
        os.chdir(BUILD_DIR)
        print(f"📁 Serving from: {BUILD_DIR}")
    else:
        print(f"❌ Build directory not found: {BUILD_DIR}")
        print("   Run 'jenga build --platform web-wasm-emscripten' first")
        exit(1)

    # Créer le serveur
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}/GLTriangle.html"
        print(f"🌐 Server started at: {url}")
        print(f"   Press Ctrl+C to stop")

        # Ouvrir le navigateur automatiquement
        try:
            webbrowser.open(url)
        except:
            pass

        # Démarrer le serveur
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✓ Server stopped")
