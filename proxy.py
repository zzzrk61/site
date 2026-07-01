#!/usr/bin/env python3
"""
VoidTrace Proxy Server — BrixHub Integration
Lance avec : python proxy.py
Accès site  : http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes

# ════ CONFIG ════
BRIXHUB_API_KEY = "brix_q6YoXWsB4wSJgjjnv8hXJMrbc9DfYAOMTCWP9e_CSiImM0x6"
BRIXHUB_BASE    = "https://api.brixhub.ch/api/v1"
SITE_FILE       = "voidtrace-brixhub.html"
PORT            = 8000

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        path = self.path.split("?")[0]
        
        # /api/search → proxy vers BrixHub /search
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
                        "User-Agent": "VoidTrace/1.0"
                    }
                )
                
                with urllib.request.urlopen(req, timeout=15) as r:
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

        # /api/lookup/email/<email> → proxy vers BrixHub /lookup/email/{email}
        if path.startswith("/api/lookup/email/"):
            email = path.split("/api/lookup/email/")[1].strip("/")
            return self._brixhub_lookup("email", email)

        # /api/lookup/phone/<phone> → proxy vers BrixHub /lookup/phone/{phone}
        if path.startswith("/api/lookup/phone/"):
            phone = path.split("/api/lookup/phone/")[1].strip("/")
            return self._brixhub_lookup("phone", phone)

        # /api/lookup/iban/<iban> → proxy vers BrixHub /lookup/iban/{iban}
        if path.startswith("/api/lookup/iban/"):
            iban = path.split("/api/lookup/iban/")[1].strip("/")
            return self._brixhub_lookup("iban", iban)

        # Fichiers statiques (HTML, CSS, JS)
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
            self.send_header("Content-Type", "text/plain")
            self.send_cors()
            self.end_headers()
            self.wfile.write(b"Not found")

    def _brixhub_lookup(self, lookup_type, query):
        """Proxy générique vers les endpoints /lookup de BrixHub"""
        try:
            url = f"{BRIXHUB_BASE}/lookup/{lookup_type}/{urllib.parse.quote(query)}"
            req = urllib.request.Request(url, 
                headers={
                    "X-API-Key": BRIXHUB_API_KEY,
                    "User-Agent": "VoidTrace/1.0"
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as r:
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

    def _json_err(self, code, msg):
        body = json.dumps({"status":"error", "message": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    print(f"\n  ⚡ VoidTrace Proxy Server")
    print(f"  → http://localhost:{PORT}")
    print(f"  📄 Fichier HTML: {SITE_FILE}")
    print(f"  🔑 API Key: {BRIXHUB_API_KEY[:20]}...")
    print(f"  ✓ Endpoints: /api/search, /api/lookup/email, /api/lookup/phone, /api/lookup/iban")
    print(f"  Ctrl+C pour arrêter\n")
    
    try:
        HTTPServer(("", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n\n  ✓ Serveur arrêté")
