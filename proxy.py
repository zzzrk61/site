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
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            f.write("{}")
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def today_str():
    return datetime.date.today().isoformat()

# ════ Handler ════
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[LOG] {self.address_string()} — {fmt % args}")

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
                    return self.json_out(400, {"ok": False, "error": "Username minimum 3 caractères"})
                if not all(c.isalnum() or c == '_' for c in u):
                    return self.json_out(400, {"ok": False, "error": "Username: lettres, chiffres et _ uniquement"})
                if len(p) < 6:
                    return self.json_out(400, {"ok": False, "error": "Mot de passe minimum 6 caractères"})

                users = load_users()
                if u in users:
                    return self.json_out(400, {"ok": False, "error": "Ce username est déjà pris"})

                is_admin = (u == ADMIN_USERNAME)
                users[u] = {
                    "username": u,
                    "password": hash_pass(p),
                    "apiKey": gen_api_key(u),
                    "plan": "enterprise" if is_admin else "free",
                    "permissions": {
                        "discord": is_admin,
                        "ip": is_admin,
                        "info": is_admin,
                        "fivem": is_admin,
                        "breach": is_admin
                    },
                    "isAdmin": is_admin,
                    "createdAt": today_str(),
                    "reqToday": 0,
                    "reqTotal": 0,
                    "lastReqDay": today_str()
                }
                save_users(users)
                user_pub = {k: v for k, v in users[u].items() if k != "password"}
                return self.json_out(200, {"ok": True, "user": user_pub})

            except Exception as e:
                return self.json_out(500, {"ok": False, "error": str(e)})

        # LOGIN
        if path == "/auth/login":
            try:
                body = json.loads(self.read_body())
                u = body.get("username", "").strip().lower()
                p = body.get("password", "")
                users = load_users()
                user = users.get(u)

                if not user or user["password"] != hash_pass(p):
                    return self.json_out(401, {"ok": False, "error": "Username ou mot de passe incorrect"})

                if user.get("lastReqDay") != today_str():
                    user["reqToday"] = 0
                    user["lastReqDay"] = today_str()
                    users[u] = user
                    save_users(users)

                user_pub = {k: v for k, v in user.items() if k != "password"}
                return self.json_out(200, {"ok": True, "user": user_pub})

            except Exception as e:
                return self.json_out(500, {"ok": False, "error": str(e)})

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
                        return self.json_out(200, {"ok": True, "apiKey": user["apiKey"]})

                return self.json_out(403, {"ok": False, "error": "Clé invalide"})

            except Exception as e:
                return self.json_out(500, {"ok": False, "error": str(e)})

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
                    return self.json_out(403, {"ok": False, "error": "Non autorisé"})
                if target not in users:
                    return self.json_out(404, {"ok": False, "error": "User introuvable"})

                users[target]["plan"] = plan
                save_users(users)
                return self.json_out(200, {"ok": True})

            except Exception as e:
                return self.json_out(500, {"ok": False, "error": str(e)})

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
                    return self.json_out(403, {"ok": False, "error": "Non autorisé"})
                if target not in users:
                    return self.json_out(404, {"ok": False, "error": "User introuvable"})

                users[target]["permissions"][perm] = val
                save_users(users)
                return self.json_out(200, {"ok": True})

            except Exception as e:
                return self.json_out(500, {"ok": False, "error": str(e)})

        # ADMIN: delete user
        if path == "/admin/delete-user":
            try:
                body = json.loads(self.read_body())
                admin_key = body.get("adminKey", "")
                target = body.get("username", "")

                users = load_users()
                admin = next((u for u in users.values() if u.get("apiKey") == admin_key and u.get("isAdmin")), None)

                if not admin:
                    return self.json_out(403, {"ok": False, "error": "Non autorisé"})

                if target in users:
                    del users[target]
                    save_users(users)

                return self.json_out(200, {"ok": True})

            except Exception as e:
                return self.json_out(500, {"ok": False, "error": str(e)})

        self.send_response(404)
        self.end_headers()
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
            return

        # Si fichier introuvable
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.cors()
        self.end_headers()
        self.wfile.write(b"Not found")

    # ════ Verification & Tracking ════
    def verify(self, vt_key, permission):
        if not vt_key:
            return False, "Clé API manquante", None

        users = load_users()
        for u, user in users.items():
            if user.get("apiKey") == vt_key:

                # Reset journalier
                if user.get("lastReqDay") != today_str():
                    user["reqToday"] = 0
                    user["lastReqDay"] = today_str()
                    save_users(users)

                # Admin bypass
                if user.get("isAdmin"):
                    return True, "ok", user

                # Permissions
                if not user.get("permissions", {}).get(permission, False):
                    return False, f"Permission '{permission}' non activée", None

                # Quota
                limit = PLANS.get(user.get("plan", "free"), 100)
                if user.get("reqToday", 0) >= limit:
                    return False, f"Quota journalier atteint ({limit} req/jour)", None

                return True, "ok", user

        return False, "Clé API invalide", None

    def track(self, user):
        if not user:
            return
        users = load_users()
        u = user["username"]

        if u not in users:
            return

        # Reset journalier
        if users[u].get("lastReqDay") != today_str():
            users[u]["reqToday"] = 0
            users[u]["lastReqDay"] = today_str()

        users[u]["reqToday"] = users[u].get("reqToday", 0) + 1
        users[u]["reqTotal"] = users[u].get("reqTotal", 0) + 1
        save_users(users)


# ════ Main server ════
if __name__ == "__main__":
    print("\n  🔍 VoidTrace Proxy Server")
    print(f"  Port: {PORT}")
    print("  APIs: Cord.cat (Discord), IP-API, BrixHub")
    print(f"  Listening on 0.0.0.0:{PORT}\n")

    try:
        HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n  Arrêté.")
        sys.exit(0)
