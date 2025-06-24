#!/usr/bin/env python3
import http.server
import socketserver
import os
from pathlib import Path

PORT = 5174
DIRECTORY = "dist"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cross-Origin-Embedder-Policy', 'cross-origin')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        super().end_headers()

os.chdir(Path(__file__).parent)
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()