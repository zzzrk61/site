#!/usr/bin/env python3
"""
VoidTrace Proxy Server — BrixHub Integration
Lance avec : python proxy.py
Accès : http://localhost:8000 (local) ou https://votre-domain.onrender.com (Render)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes, sys

# ════ CONFIG ════
BRIXHUB_API_KEY = "brix_q6YoXWsB4wSJgjjnv8hXJMrbc9DfYAOMTCWP9e_CSiImM0x6"
BRIXHUB_BASE    = "https://api.brixhub.ch/api/v1"
SITE_FILE       = "voidtrace-brixhub.html"
PORT            = int(os.environ.get('PORT', 8000))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}", file=sys.stdout, flush=True)

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
        
        # POST /api/search → proxy vers BrixHub /search
        if path == "/api/search":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                search_data = json.loads(body)
                
                # Ajouter les paramètres BrixHub par défaut
                if 'flexible' not in search_data:
                    search_data['flexible'] = True
                if 'per_page' not in search_data:
                    search_data['per_page'] = 50
                
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

        # GET /api/lookup/email/<email> → proxy vers BrixHub /lookup/email/{email}
        if path.startswith("/api/lookup/email/"):
            email = path.split("/api/lookup/email/")[1].strip("/")
            return self._brixhub_lookup("email", email)

        # GET /api/lookup/phone/<phone> → proxy vers BrixHub /lookup/phone/{phone}
        if path.startswith("/api/lookup/phone/"):
            phone = path.split("/api/lookup/phone/")[1].strip("/")
            return self._brixhub_lookup("phone", phone)

        # GET /api/lookup/iban/<iban> → proxy vers BrixHub /lookup/iban/{iban}
        if path.startswith("/api/lookup/iban/"):
            iban = path.split("/api/lookup/iban/")[1].strip("/")
            return self._brixhub_lookup("iban", iban)

        # Fichiers statiques (HTML, CSS, JS)
        if path == "/" or path == "/index.html":
            path = "/" + SITE_FILE
        
        filepath = path.lstrip("/")
        
        # Chercher le fichier HTML
        search_paths = [
            filepath,
            f"/mnt/user-data/outputs/{filepath}",
            f"./{filepath}",
            os.path.join(os.path.dirname(__file__), filepath)
        ]
        
        actual_path = None
        for candidate in search_paths:
            if os.path.isfile(candidate):
                actual_path = candidate
                break
        
        if actual_path:
            try:
                mime, _ = mimetypes.guess_type(actual_path)
                self.send_response(200)
                self.send_header("Content-Type", mime or "text/html; charset=utf-8")
                self.send_cors()
                
                # Lire la taille du fichier
                file_size = os.path.getsize(actual_path)
                self.send_header("Content-Length", str(file_size))
                self.end_headers()
                
                with open(actual_path, "rb") as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.send_cors()
                self.end_headers()
                self.wfile.write(f"500 Error: {str(e)}".encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_cors()
            self.end_headers()
            self.wfile.write(f"404 Not Found".encode())

    def _brixhub_lookup(self, lookup_type, query):
        """Proxy vers les endpoints /lookup de BrixHub"""
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
    print(f"  🌐 http://localhost:{PORT}")
    print(f"  📄 Fichier: {SITE_FILE}")
    print(f"  🔑 API: {BRIXHUB_API_KEY[:20]}...")
    print(f"  ✓ Endpoints: /api/search, /api/lookup/*")
    print(f"  ⏹  Ctrl+C pour arrêter\n")
    
    try:
        server = HTTPServer(("0.0.0.0", PORT), Handler)
        print(f"  ✓ Serveur lancé sur le port {PORT}\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n  ✓ Serveur arrêté")
    except Exception as e:
        print(f"\n  ✗ Erreur: {e}")
        sys.exit(1)
