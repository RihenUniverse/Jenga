#!/usr/bin/env python3
"""
Serveur HTTP local générique pour tester les applications Emscripten
Usage:
  python run_web.py                           # Auto-détecte le dernier build
  python run_web.py path/to/build/dir        # Dossier spécifique
  python run_web.py --port 8888              # Port personnalisé
"""
import http.server
import socketserver
import webbrowser
import sys
from pathlib import Path

# Configuration par défaut
DEFAULT_PORT = 8080

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP avec headers CORS pour WebAssembly"""

    def end_headers(self):
        # Headers CORS pour SharedArrayBuffer et WebAssembly
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def guess_type(self, path):
        """Ajouter le type MIME correct pour .wasm"""
        if path.endswith('.wasm'):
            return 'application/wasm'
        return super().guess_type(path)

def find_build_dir(start_path=None):
    """Trouve automatiquement le répertoire de build Emscripten"""
    search_paths = []

    if start_path:
        search_paths.append(Path(start_path))
    else:
        # Chercher depuis le répertoire courant
        cwd = Path.cwd()
        search_paths.extend([
            cwd / "Build" / "Bin" / "Debug-Web",
            cwd / "Build" / "Bin" / "Release-Web",
        ])

        # Chercher récursivement dans Build/
        if (cwd / "Build").exists():
            for p in (cwd / "Build").rglob("*.html"):
                search_paths.append(p.parent)

    # Retourner le premier répertoire contenant un .html
    for path in search_paths:
        if path.exists():
            html_files = list(path.glob("*.html"))
            if html_files:
                return path, html_files[0].name

    return None, None

def main():
    port = DEFAULT_PORT
    build_dir = None

    # Parse arguments
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == '--port' and i + 1 < len(args):
            port = int(args[i + 1])
        elif not arg.startswith('--') and arg.isdigit() == False:
            build_dir = Path(arg)

    # Trouver le répertoire de build
    if not build_dir:
        build_dir, html_file = find_build_dir()
    else:
        html_files = list(build_dir.glob("*.html"))
        html_file = html_files[0].name if html_files else None

    if not build_dir or not build_dir.exists():
        print("❌ No Emscripten build directory found")
        print("\nUsage:")
        print("  python run_web.py                      # Auto-detect")
        print("  python run_web.py Build/Bin/Debug-Web/MyApp")
        print("  python run_web.py --port 8888")
        print("\nMake sure to build first:")
        print("  jenga build --platform web-wasm-emscripten")
        return 1

    # Changer vers le répertoire de build
    import os
    os.chdir(build_dir)

    print(f"📁 Serving: {build_dir.resolve()}")
    if html_file:
        print(f"📄 Entry:   {html_file}")

    # Créer le serveur
    with socketserver.TCPServer(("", port), CORSHTTPRequestHandler) as httpd:
        url = f"http://localhost:{port}/"
        if html_file:
            url += html_file

        print(f"🌐 Server:  {url}")
        print(f"\n   Press Ctrl+C to stop\n")

        # Ouvrir le navigateur
        try:
            webbrowser.open(url)
            print(f"✓ Browser opened")
        except:
            print(f"⚠ Could not open browser automatically")
            print(f"  Open manually: {url}")

        # Démarrer le serveur
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✓ Server stopped")
            return 0

if __name__ == '__main__':
    sys.exit(main())
