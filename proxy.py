#!/usr/bin/env python3
"""
VoidTrace Proxy Server
Lance avec : python voidtrace_proxy.py
Accès site  : http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes

CORDCAT_API_KEY = "cc_4620fd6426ade7188865631415209cf36c002089ee909b06"
CORDCAT_BASE    = "https://api.cord.cat"
IPAPI_BASE      = "http://ip-api.com/json"
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

        # POST /api/search → CordCat Discord + ip-api.com
        if path == "/api/search":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                search_data = json.loads(body)
                
                results = {"data": {}}
                
                # Lookup Discord ID
                if "discord_id" in search_data and search_data["discord_id"]:
                    discord_id = search_data["discord_id"]
                    url = f"{CORDCAT_BASE}/api/v2/query/{discord_id}"
                    req = urllib.request.Request(url, headers={
                        "X-API-Key": CORDCAT_API_KEY,
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    })
                    try:
                        with urllib.request.urlopen(req, timeout=10) as r:
                            discord_data = json.loads(r.read().decode())
                            results["data"]["discord"] = discord_data
                    except Exception as e:
                        results["data"]["discord"] = {"error": str(e)}
                
                # Lookup IP
                if "ip" in search_data and search_data["ip"]:
                    ip = search_data["ip"]
                    url = f"{IPAPI_BASE}?query={ip}&fields=status,country,city,lat,lon,isp,org,as"
                    req = urllib.request.Request(url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    })
                    try:
                        with urllib.request.urlopen(req, timeout=10) as r:
                            ip_data = json.loads(r.read().decode())
                            results["data"]["ip"] = ip_data
                    except Exception as e:
                        results["data"]["ip"] = {"error": str(e)}
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())
                
            except Exception as e:
                self._json_err(500, str(e))
            return

    def do_GET(self):
        path = self.path.split("?")[0]

        # /api/lookup/discord/<id> → CordCat
        if path.startswith("/api/lookup/discord/"):
            discord_id = path.split("/api/lookup/discord/")[1].strip("/")
            url = f"{CORDCAT_BASE}/api/v2/query/{discord_id}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": CORDCAT_API_KEY,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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

        # /api/lookup/ip/<ip> → ip-api.com
        if path.startswith("/api/lookup/ip/"):
            ip = path.split("/api/lookup/ip/")[1].strip("/")
            url = f"{IPAPI_BASE}?query={ip}&fields=status,country,city,lat,lon,isp,org,as"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
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
    print(f"  API CordCat    : {CORDCAT_API_KEY[:20]}...")
    print(f"  IP API         : ip-api.com")
    print(f"  Endpoints      : /api/search, /api/lookup/discord, /api/lookup/ip")
    print(f"  Ctrl+C pour arrêter\n")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
