#!/usr/bin/env python3

"""
VoidTrace Proxy Server

Lance avec : python proxy.py
Accès site : http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes

API_KEY_DISCORD = "cc_8b7545d8d46432196c93142dbeba9665e062217d459e1f5d"
SITE_FILE = "voidtrace-full.html"
PORT = int(os.environ.get('PORT', 8000))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f" {self.address_string()} — {fmt % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        # /api/discord/<id> → proxy vers CordCat
        if path.startswith("/api/discord/"):
            uid = path.split("/api/discord/")[1].strip("/")
            url = f"https://api.cord.cat/api/v2/query/{uid}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": API_KEY_DISCORD,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Origin": "https://cord.cat",
                "Referer": "https://cord.cat/"
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
                try:
                    body = e.read()
                except:
                    body = b'{"status":"fail"}'
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._json_err(500, str(e))
            return

        # /api/ip/<address> → proxy CORS pour ip-api.com
        if path.startswith("/api/ip/"):
            ip = path.split("/api/ip/")[1].strip("/")
            url = f"http://ip-api.com/json/{ip}?fields=66846719"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json",
            })

            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                # Fallback freeipapi
                try:
                    url2 = f"https://freeipapi.com/api/json/{ip}"
                    req2 = urllib.request.Request(url2, headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
                    with urllib.request.urlopen(req2, timeout=10) as r2:
                        raw = json.loads(r2.read())
                        out = {
                            "status": "success",
                            "query": raw.get("ipAddress", ip),
                            "country": raw.get("countryName",""),
                            "countryCode": raw.get("countryCode",""),
                            "regionName": raw.get("regionName",""),
                            "city": raw.get("cityName",""),
                            "zip": raw.get("zipCode",""),
                            "lat": raw.get("latitude",0),
                            "lon": raw.get("longitude",0),
                            "timezone": raw.get("timeZone",""),
                            "isp": raw.get("ipVersion",""),
                            "org": "",
                            "as": "",
                            "asname": "",
                            "reverse": "",
                            "mobile": False,
                            "proxy": False,
                            "hosting": False,
                            "currency": raw.get("currency",{}).get("code","") if isinstance(raw.get("currency"),dict) else ""
                        }
                        body = json.dumps(out).encode()
                        self.send_response(200)
                        self.send_header("Content-Type","application/json")
                        self.send_cors()
                        self.end_headers()
                        self.wfile.write(body)
                except Exception as e2:
                    self._json_err(500, f"IP lookup failed")
            return

        # Fichiers statiques
        if path == "/" or path == "/index.html":
            path = "/" + SITE_FILE

        filepath = path.lstrip("/")
        
        # Cherche dans : local, outputs, current dir
        search_paths = [filepath, f"./{filepath}", f"/mnt/user-data/outputs/{filepath}"]
        actual_path = None
        
        for candidate in search_paths:
            if os.path.isfile(candidate):
                actual_path = candidate
                break

        if actual_path:
            mime, _ = mimetypes.guess_type(actual_path)
            try:
                self.send_response(200)
                self.send_header("Content-Type", mime or "text/plain")
                self.send_cors()
                self.end_headers()
                with open(actual_path, "rb") as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self._json_err(500, str(e))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_cors()
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
    print(f"\n VoidTrace Proxy — http://localhost:{PORT}")
    print(f" Fichier: {SITE_FILE}")
    print(f" Ctrl+C pour arrêter\n")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
