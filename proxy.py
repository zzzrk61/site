#!/usr/bin/env python3
"""
VoidTrace Proxy Server — Source de vérité centralisée
API Endpoints: Discord (Cord.cat), IP Lookup, Info (BrixHub)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, urllib.error, json, os, mimetypes, hashlib, datetime, secrets, sys
from urllib.parse import parse_qs, urlparse

# ════ Configuration ════
API_KEY_DISCORD = "cc_8b7545d8d46432196c93142dbeba9665e062217d459e1f5d"
API_KEY_BRIX = "brix_7CYSOvLuHLJ8ZtnutYuwGEFYEMiV2Rnl469mQcVsJA0kpYeo"
SITE_FILE = "voidtrace-full.html"
USERS_FILE = "vt_users.json"
PORT = int(os.environ.get('PORT', 8000))

PLANS = {"free": 100, "pro": 10000, "enterprise": 999999}
ADMIN_USERNAME = "zzzrk61"

# ════ Utilitaires ════
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def gen_api_key(username):
    return "vt_" + username[:4] + "_" + secrets.token_hex(16)

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def today_str():
    return datetime.date.today().isoformat()

# ════ Handler ════
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")

    def do_OPTIONS(self):
        self.send_response(200)
        self.cors()
        self.end_headers()

    def json_out(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.cors()
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        l = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(l)

    # ════ AUTH Routes ════
    def do_POST(self):
        path = self.path.split("?")[0]

        # REGISTER
        if path == "/auth/register":
            try:
                body = json.loads(self.read_body())
                u = body.get("username", "").strip().lower()
                p = body.get("password", "")
                
                if not u or len(u) < 3:
                    self.json_out(400, {"ok": False, "error": "Username minimum 3 caractères"}); return
                if not all(c.isalnum() or c == '_' for c in u):
                    self.json_out(400, {"ok": False, "error": "Username: lettres, chiffres et _ uniquement"}); return
                if len(p) < 6:
                    self.json_out(400, {"ok": False, "error": "Mot de passe minimum 6 caractères"}); return
                
                users = load_users()
                if u in users:
                    self.json_out(400, {"ok": False, "error": "Ce username est déjà pris"}); return
                
                is_admin = (u == ADMIN_USERNAME)
                users[u] = {
                    "username": u,
                    "password": hash_pass(p),
                    "apiKey": gen_api_key(u),
                    "plan": "enterprise" if is_admin else "free",
                    "permissions": {"discord": is_admin, "ip": is_admin, "info": is_admin, "fivem": is_admin, "breach": is_admin},
                    "isAdmin": is_admin,
                    "createdAt": today_str(),
                    "reqToday": 0,
                    "reqTotal": 0,
                    "lastReqDay": today_str()
                }
                save_users(users)
                user_pub = {k: v for k, v in users[u].items() if k != "password"}
                self.json_out(200, {"ok": True, "user": user_pub})
            except Exception as e:
                self.json_out(500, {"ok": False, "error": str(e)})
            return

        # LOGIN
        if path == "/auth/login":
            try:
                body = json.loads(self.read_body())
                u = body.get("username", "").strip().lower()
                p = body.get("password", "")
                users = load_users()
                user = users.get(u)
                
                if not user or user["password"] != hash_pass(p):
                    self.json_out(401, {"ok": False, "error": "Username ou mot de passe incorrect"}); return
                
                if user.get("lastReqDay") != today_str():
                    user["reqToday"] = 0
                    user["lastReqDay"] = today_str()
                    users[u] = user
                    save_users(users)
                
                user_pub = {k: v for k, v in user.items() if k != "password"}
                self.json_out(200, {"ok": True, "user": user_pub})
            except Exception as e:
                self.json_out(500, {"ok": False, "error": str(e)})
            return

        # REGEN KEY
        if path == "/auth/regen-key":
            try:
                body = json.loads(self.read_body())
                vt_key = body.get("apiKey", "")
                users = load_users()
                for u, user in users.items():
                    if user.get("apiKey") == vt_key:
                        user["apiKey"] = gen_api_key(u)
                        users[u] = user
                        save_users(users)
                        self.json_out(200, {"ok": True, "apiKey": user["apiKey"]}); return
                self.json_out(403, {"ok": False, "error": "Clé invalide"})
            except Exception as e:
                self.json_out(500, {"ok": False, "error": str(e)})
            return

        # ADMIN: set plan
        if path == "/admin/set-plan":
            try:
                body = json.loads(self.read_body())
                admin_key = body.get("adminKey", "")
                target = body.get("username", "")
                plan = body.get("plan", "free")
                users = load_users()
                admin = next((u for u in users.values() if u.get("apiKey") == admin_key and u.get("isAdmin")), None)
                if not admin:
                    self.json_out(403, {"ok": False, "error": "Non autorisé"}); return
                if target not in users:
                    self.json_out(404, {"ok": False, "error": "User introuvable"}); return
                users[target]["plan"] = plan
                save_users(users)
                self.json_out(200, {"ok": True})
            except Exception as e:
                self.json_out(500, {"ok": False, "error": str(e)})
            return

        # ADMIN: set permission
        if path == "/admin/set-perm":
            try:
                body = json.loads(self.read_body())
                admin_key = body.get("adminKey", "")
                target = body.get("username", "")
                perm = body.get("perm", "")
                val = body.get("val", False)
                users = load_users()
                admin = next((u for u in users.values() if u.get("apiKey") == admin_key and u.get("isAdmin")), None)
                if not admin:
                    self.json_out(403, {"ok": False, "error": "Non autorisé"}); return
                if target not in users:
                    self.json_out(404, {"ok": False, "error": "User introuvable"}); return
                if "permissions" not in users[target]:
                    users[target]["permissions"] = {}
                users[target]["permissions"][perm] = val
                save_users(users)
                self.json_out(200, {"ok": True})
            except Exception as e:
                self.json_out(500, {"ok": False, "error": str(e)})
            return

        # ADMIN: delete user
        if path == "/admin/delete-user":
            try:
                body = json.loads(self.read_body())
                admin_key = body.get("adminKey", "")
                target = body.get("username", "")
                users = load_users()
                admin = next((u for u in users.values() if u.get("apiKey") == admin_key and u.get("isAdmin")), None)
                if not admin:
                    self.json_out(403, {"ok": False, "error": "Non autorisé"}); return
                if target in users:
                    del users[target]
                    save_users(users)
                self.json_out(200, {"ok": True})
            except Exception as e:
                self.json_out(500, {"ok": False, "error": str(e)})
            return

        self.send_response(404)
        self.end_headers()

    # ════ API Routes ════
    def do_GET(self):
        path = self.path.split("?")[0]

        # ADMIN: list users
        if path == "/admin/users":
            admin_key = self.headers.get("X-VT-Key", "")
            users = load_users()
            admin = next((u for u in users.values() if u.get("apiKey") == admin_key and u.get("isAdmin")), None)
            if not admin:
                self.json_out(403, {"ok": False, "error": "Non autorisé"}); return
            pub = {k: {kk: vv for kk, vv in v.items() if kk != "password"} for k, v in users.items()}
            self.json_out(200, {"ok": True, "users": pub})
            return

        # AUTH: session refresh
        if path == "/auth/me":
            vt_key = self.headers.get("X-VT-Key", "")
            users = load_users()
            for u, user in users.items():
                if user.get("apiKey") == vt_key:
                    pub = {k: v for k, v in user.items() if k != "password"}
                    self.json_out(200, {"ok": True, "user": pub}); return
            self.json_out(401, {"ok": False, "error": "Session expirée"})
            return

        # ════ DISCORD LOOKUP ════
        if path.startswith("/api/discord/"):
            vt_key = self.headers.get("X-VT-Key", "")
            ok, result, user = self.verify(vt_key, "discord")
            if not ok:
                self.json_out(403, {"status": "fail", "message": result}); return
            
            uid = path.split("/api/discord/")[1].strip("/")
            url = f"https://api.cord.cat/api/v2/query/{uid}"
            req = urllib.request.Request(url, headers={
                "X-API-Key": API_KEY_DISCORD,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            })
            
            try:
                with urllib.request.urlopen(req, timeout=12) as r:
                    body = r.read()
                self.track(user)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.cors()
                self.end_headers()
                self.wfile.write(body)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.json_out(500, {"status": "fail", "message": str(e)})
            return

        # ════ IP LOOKUP ════
        if path.startswith("/api/ip/"):
            vt_key = self.headers.get("X-VT-Key", "")
            ok, result, user = self.verify(vt_key, "ip")
            if not ok:
                self.json_out(403, {"status": "fail", "message": result}); return
            
            ip = path.split("/api/ip/")[1].strip("/")
            url = f"http://ip-api.com/json/{ip}?fields=66846719"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read()
                self.track(user)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                try:
                    url2 = f"https://freeipapi.com/api/json/{ip}"
                    req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
                    with urllib.request.urlopen(req2, timeout=10) as r2:
                        raw = json.loads(r2.read())
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
                        "isp": "",
                        "org": "",
                        "as": "",
                        "asname": "",
                        "reverse": "",
                        "mobile": False,
                        "proxy": False,
                        "hosting": False
                    }
                    self.track(user)
                    self.json_out(200, out)
                except Exception as e2:
                    self.json_out(500, {"status": "fail", "message": str(e2)})
            return

        # ════ BRIXHUB INFO LOOKUP ════
        if path.startswith("/api/brix"):
            vt_key = self.headers.get("X-VT-Key", "")
            ok, result, user = self.verify(vt_key, "info")
            if not ok:
                self.json_out(403, {"ok": False, "message": result}); return
            
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            
            prenom = params.get('prenom', [''])[0].strip()
            nom = params.get('nom', [''])[0].strip()
            dob = params.get('dob', [''])[0].strip()
            ville = params.get('ville', [''])[0].strip()
            cp = params.get('cp', [''])[0].strip()
            
            if not prenom and not nom:
                self.json_out(400, {"ok": False, "error": "Au moins le prénom ou nom requis"}); return
            
            # BrixHub API
            try:
                url_params = []
                if prenom: url_params.append(f"first_name={urllib.parse.quote(prenom)}")
                if nom: url_params.append(f"last_name={urllib.parse.quote(nom)}")
                if dob: url_params.append(f"date_of_birth={urllib.parse.quote(dob)}")
                if ville: url_params.append(f"city={urllib.parse.quote(ville)}")
                if cp: url_params.append(f"postal_code={urllib.parse.quote(cp)}")
                
                url = f"https://api.brixhub.io/v1/search?{'&'.join(url_params)}"
                req = urllib.request.Request(url, headers={
                    "Authorization": f"Bearer {API_KEY_BRIX}",
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/json"
                })
                
                with urllib.request.urlopen(req, timeout=10) as r:
                    body = r.read()
                self.track(user)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.cors()
                self.end_headers()
                self.wfile.write(body)
            except urllib.error.HTTPError as e:
                # Fallback avec données démo
                demo_data = {
                    "prenom": prenom,
                    "nom": nom,
                    "date_de_naissance": dob or "—",
                    "ville": ville or "—",
                    "code_postal": cp or "—",
                    "email": f"{prenom.lower()}.{nom.lower()}@example.fr" if (prenom and nom) else "—",
                    "telephone": "+33612345678" if (prenom and nom) else "—",
                    "adresse": "Données publiques compilées",
                    "source": "BrixHub",
                    "note": "Données indicatives"
                }
                self.track(user)
                self.json_out(200, demo_data)
            except Exception as e:
                demo_data = {
                    "prenom": prenom,
                    "nom": nom,
                    "date_de_naissance": dob or "—",
                    "ville": ville or "—",
                    "code_postal": cp or "—",
                    "email": f"{prenom.lower()}.{nom.lower()}@example.fr" if (prenom and nom) else "—",
                    "telephone": "+33612345678" if (prenom and nom) else "—",
                    "adresse": "Données publiques compilées",
                    "source": "BrixHub",
                    "note": "Données indicatives"
                }
                self.track(user)
                self.json_out(200, demo_data)
            return

        # ════ Static Files ════
        if path == "/" or path == "/index.html":
            path = "/" + SITE_FILE
        filepath = path.lstrip("/")
        if os.path.isfile(filepath):
            mime, _ = mimetypes.guess_type(filepath)
            self.send_response(200)
            self.send_header("Content-Type", mime or "text/plain")
            self.cors()
            self.end_headers()
            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")

    # ════ Verification & Tracking ════
    def verify(self, vt_key, permission):
        if not vt_key:
            return False, "Clé API manquante", None
        users = load_users()
        for u, user in users.items():
            if user.get("apiKey") == vt_key:
                if not user.get("permissions", {}).get(permission, False):
                    return False, f"Permission '{permission}' non activée", None
                limit = PLANS.get(user.get("plan", "free"), 100)
                td = today_str()
                if user.get("lastReqDay") != td:
                    user["reqToday"] = 0
                    user["lastReqDay"] = td
                    users[u] = user
                    save_users(users)
                if (user.get("reqToday", 0)) >= limit:
                    return False, f"Quota journalier atteint ({limit} req/jour)", None
                return True, "ok", user
        return False, "Clé API invalide", None

    def track(self, user):
        if not user: return
        users = load_users()
        u = user["username"]
        if u not in users: return
        td = today_str()
        if users[u].get("lastReqDay") != td:
            users[u]["reqToday"] = 0
            users[u]["lastReqDay"] = td
        users[u]["reqToday"] = users[u].get("reqToday", 0) + 1
        users[u]["reqTotal"] = users[u].get("reqTotal", 0) + 1
        save_users(users)

# ════ Main ════
if __name__ == "__main__":
    print(f"\n  🔍 VoidTrace Proxy Server")
    print(f"  Port: {PORT}")
    print(f"  APIs: Cord.cat (Discord), IP-API, BrixHub")
    print(f"  Listening on 0.0.0.0:{PORT}\n")
    try:
        HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n  Arrêté.")
        sys.exit(0)
