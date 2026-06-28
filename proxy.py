#!/usr/bin/env python3
"""
VoidTrace Proxy Server
Lance avec : python proxy.py
Accès site  : http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes

API_KEY_DISCORD = "cc_8b7545d8d46432196c93142dbeba9665e062217d459e1f5d"
API_KEY_BRIXHUB = "brix_vplzbbZhnCZy-gmJFMoJ78xFYYyUGjxfnQYA3OURtXqbEFd8"  # <-- Ajoute ta clé API ici
SITE_FILE       = "voidtrace-full.html"
PORT            = 8000

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

    def do_GET(self):
        path = self.path.split("?")[0]

        # Proxy vers CordCat
        if path.startswith("/api/discord/"):
            uid = path.split("/api/discord/")[1].strip("/")
            url = f"https://api.cord.cat/api/v2/query/{uid}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": API_KEY_DISCORD,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
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
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._json_err(500, str(e))
            return

        # Proxy vers IP-API / fallback à freeipapi
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
            except urllib.error.HTTPError as e:
                # fallback à freeipapi
                try:
                    url2 = f"https://freeipapi.com/api/json/{ip}"
                    req2 = urllib.request.Request(url2, headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
                    with urllib.request.urlopen(req2, timeout=10) as r2:
                        raw = json.loads(r2.read())
                    # Normaliser vers format ip-api
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
                    self._json_err(500, f"ip-api: {e}, fallback: {e2}")
            except Exception as e:
                self._json_err(500, str(e))
            return

        # Proxy vers BrixHub API
        if path.startswith("/api/brixhub/") or path.startswith("/api/search") or path.startswith("/api/v1/"):
            # Utilisation de la clé API BrixHub
            url = f"https://api.brixhub.ch{path}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": API_KEY_BRIXHUB,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            })
            # Si c'est une requête POST, il faut gérer aussi (si nécessaire)
            # Mais ici, pour GET, c'est suffisant
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read()
                self.send_response(r.getcode())
                self.send_header("Content-Type", r.getheader("Content-Type") or "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
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
    print(f"  Ctrl+C pour arrêter\n")
    HTTPServer(("", PORT), Handler).serve_forever()
