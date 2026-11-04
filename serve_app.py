#!/usr/bin/env python3
"""
Serveur local léger pour l'application Album Famille Fontenay (port 8765)
avec bouton de synchronisation automatique depuis WhatsApp Mac / iCloud.
"""
import subprocess
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_DIR = Path("/Users/thomaslefevre/.t3/projects/photo-famille")
PORT = 8765

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_DIR), **kwargs)

    def do_POST(self):
        if self.path == "/api/resync":
            try:
                subprocess.run([sys.executable, str(PROJECT_DIR / "extract_whatsapp_photos.py")], check=True)
                bin_path = PROJECT_DIR / "analyze_vision"
                if not bin_path.exists():
                    subprocess.run(["swiftc", "-O", str(PROJECT_DIR / "analyze_vision.swift"), "-o", str(bin_path)], check=True)
                subprocess.run([str(bin_path)], check=True)
                subprocess.run([sys.executable, str(PROJECT_DIR / "build_catalog_and_themes.py")], check=True)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(f'{{"status":"error","message":"{e}"}}'.encode("utf-8"))
        else:
            self.send_error(404)

def main():
    url = f"http://localhost:{PORT}"
    print(f"✨ Album Famille Fontenay disponible sur {url}")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")

if __name__ == "__main__":
    main()
