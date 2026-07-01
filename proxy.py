#!/usr/bin/env python3
"""
VoidTrace Proxy Server
Lance avec : python proxy.py
Accès site  : http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes

BRIXHUB_API_KEY = "brix_q6YoXWsB4wSJgjjnv8hXJMrbc9DfYAOMTCWP9e_CSiImM0x6"
BRIXHUB_BASE    = "https://api.brixhub.ch/api/v1"
SITE_FILE       = "voidtrace-full.html"
PORT            = int(os.environ.get('PORT', 8000))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        path = self.path.split("?")[0]

        # POST /api/search → proxy vers BrixHub
        if path == "/api/search":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                search_data = json.loads(body)
                
                url = f"{BRIXHUB_BASE}/search"
                req = urllib.request.Request(url, 
                    data=json.dumps(search_data).encode(),
                    headers={
                        "X-API-Key": BRIXHUB_API_KEY,
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    }
                )
                
                with urllib.request.urlopen(req, timeout=10) as r:
                    response_body = r.read()
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(response_body)
                
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._json_err(500, str(e))
            return

    def do_GET(self):
        path = self.path.split("?")[0]

        # /api/lookup/email/<email> → proxy vers BrixHub
        if path.startswith("/api/lookup/email/"):
            email = path.split("/api/lookup/email/")[1].strip("/")
            url = f"{BRIXHUB_BASE}/lookup/email/{email}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": BRIXHUB_API_KEY,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json"
            })
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._json_err(500, str(e))
            return

        # /api/lookup/phone/<phone> → proxy vers BrixHub
        if path.startswith("/api/lookup/phone/"):
            phone = path.split("/api/lookup/phone/")[1].strip("/")
            url = f"{BRIXHUB_BASE}/lookup/phone/{phone}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": BRIXHUB_API_KEY,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json"
            })
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._json_err(500, str(e))
            return

        # /api/lookup/iban/<iban> → proxy vers BrixHub
        if path.startswith("/api/lookup/iban/"):
            iban = path.split("/api/lookup/iban/")[1].strip("/")
            url = f"{BRIXHUB_BASE}/lookup/iban/{iban}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": BRIXHUB_API_KEY,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json"
            })
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._json_err(500, str(e))
            return

        # Fichiers statiques
        if path == "/" or path == "/index.html":
            path = "/" + SITE_FILE
        filepath = path.lstrip("/")
        if os.path.isfile(filepath):
            mime, _ = mimetypes.guess_type(filepath)
            self.send_response(200)
            self.send_header("Content-Type", mime or "text/plain")
            self.send_cors()
            self.end_headers()
            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    def _json_err(self, code, msg):
        body = json.dumps({"status":"fail","message": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print(f"\n  VoidTrace Proxy — http://localhost:{PORT}")
    print(f"  Fichier servi  : {SITE_FILE}")
    print(f"  API BrixHub    : {BRIXHUB_API_KEY[:20]}...")
    print(f"  Endpoints      : /api/search, /api/lookup/email, /api/lookup/phone, /api/lookup/iban")
    print(f"  Ctrl+C pour arrêter\n")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
