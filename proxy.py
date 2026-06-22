#!/usr/bin/env python3
"""
VoidTrace Proxy Server — Version Optimisée
Lance avec : python proxy.py
Accès : http://localhost:8000
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes

# ==========================
# CONFIG
# ==========================
API_KEY_DISCORD = "cc_8b7545d8d46432196c93142dbeba9665e062217d459e1f5d"
API_KEY_BRIX    = "brix_7CYSOvLuHLJ8ZtnutYuwGEFYEMiV2Rnl469mQcVsJA0kpYeo"

SITE_FILE = "voidtrace-full.html"
PORT      = 8000


# ==========================
# HANDLER
# ==========================
class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    # ==========================
    # ROUTES
    # ==========================
    def do_GET(self):
        path = self.path.split("?")[0]

        # -----------------------------------------
        # 1) API DISCORD (CordCat)
        # -----------------------------------------
        if path.startswith("/api/discord/"):
            uid = path.replace("/api/discord/", "").strip("/")
            url = f"https://api.cord.cat/api/v2/query/{uid}"

            req = urllib.request.Request(url, headers={
                "X-API-Key": API_KEY_DISCORD,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            })

            return self._proxy_request(req)

        # -----------------------------------------
        # 2) API IP (ip-api + fallback freeipapi)
        # -----------------------------------------
        if path.startswith("/api/ip/"):
            ip = path.replace("/api/ip/", "").strip("/")
            url = f"http://ip-api.com/json/{ip}?fields=66846719"

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            })

            try:
                return self._proxy_request(req)
            except:
                return self._fallback_ip(ip)

        # -----------------------------------------
        # 3) API BRIXHUB
        # -----------------------------------------
        if path.startswith("/api/brix/"):
            query = path.replace("/api/brix/", "").strip("/")
            url = f"https://brixhub.net/api/v1/search/{query}"

            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {API_KEY_BRIX}",
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            })

            return self._proxy_request(req)

        # -----------------------------------------
        # 4) FICHIERS STATIQUES
        # -----------------------------------------
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
            return

        # -----------------------------------------
        # 404
        # -----------------------------------------
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")

    # ==========================
    # HELPERS
    # ==========================
    def _proxy_request(self, req):
        """Proxy générique"""
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(body)
            return

        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(body)
            return

        except Exception as e:
            return self._json_err(500, str(e))

    def _fallback_ip(self, ip):
        """Fallback freeipapi → format ip-api"""
        try:
            url = f"https://freeipapi.com/api/json/{ip}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = json.loads(r.read())

            out = {
                "status": "success",
                "query": raw.get("ipAddress", ip),
                "country": raw.get("countryName", ""),
                "countryCode": raw.get("countryCode", ""),
                "regionName": raw.get("regionName", ""),
                "city": raw.get("cityName", ""),
                "zip": raw.get("zipCode", ""),
                "lat": raw.get("latitude", 0),
                "lon": raw.get("longitude", 0),
                "timezone": raw.get("timeZone", ""),
                "isp": raw.get("ipVersion", ""),
                "org": "",
                "as": "",
                "asname": "",
                "reverse": "",
                "mobile": False,
                "proxy": False,
                "hosting": False,
                "currency": raw.get("currency", {}).get("code", "")
            }

            body = json.dumps(out).encode()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            self._json_err(500, f"fallback error: {e}")

    def _json_err(self, code, msg):
        body = json.dumps({"status": "fail", "message": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)


# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    print(f"\n  VoidTrace Proxy — http://localhost:{PORT}")
    print(f"  Fichier servi : {SITE_FILE}")
    print("  Ctrl+C pour arrêter\n")
    HTTPServer(("", PORT), Handler).serve_forever()
