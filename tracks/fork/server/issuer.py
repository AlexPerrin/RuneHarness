#!/usr/bin/env python3
"""issuer.py: the token issuer of the test and live stacks (desktop and APK). A token is <account>.<expiry, unix seconds>.<HMAC-SHA256 of the two by the
issuer's secret, base64url>: at most 67 bytes, as the client carries it in its RSA login block (about 90 bytes; an RS256 JWT
does not fit, nor an Ed25519 signature with its account). The server's game.yml token-login block holds the secret.
  issuer.py key DIR                makes DIR/secret and DIR/tls.pem (with tls.key) once; prints the game.yml token-login block
  issuer.py mint DIR ACCOUNT [--exp S]   prints a token for ACCOUNT, expiring S seconds from now (negative: already
                                   expired); another DIR's token is a forged one
  issuer.py serve DIR              https :8080 (the desktop takes https only and trusts tls.pem) and http :8081 (the APK's
                                   LOCAL_AUTH allows cleartext), jav_config params 11 and 22: the OIDC sign-in the APK's AppAuth
                                   runs (an immediate code for DIR/account, an HS256 id_token by the secret) and game-session with
                                   the shapes RSProx records: POST sessions {idToken} -> {sessionId}; GET accounts with Bearer
                                   <sessionId> -> [{accountId, displayName, userHash}]; tokens -> {"token"} (shape unsourced; the
                                   desktop parses it): DIR/token, read at each request, else a fresh one for DIR/account
"""
import base64, hashlib, hmac, http.server, json, os, secrets, ssl, subprocess, sys, threading, time, urllib.parse, zlib
from pathlib import Path


def b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def key(d):
    d = Path(d); d.mkdir(parents=True, exist_ok=True); sec = d / "secret"
    if not sec.exists():
        sec.write_text(base64.b64encode(os.urandom(32)).decode())
    if not (d / "tls.pem").exists():
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "3650", "-subj", "/CN=127.0.0.1", "-addext",
                        "subjectAltName=IP:127.0.0.1", "-keyout", str(d / "tls.key"), "-out", str(d / "tls.pem")], check=True, capture_output=True)
    return f'token-login:\n  secret: "{sec.read_text()}"'


def sign(d, msg):
    return b64(hmac.new(base64.b64decode((Path(d) / "secret").read_text()), msg.encode(), hashlib.sha256).digest())


def mint(d, account, exp=3600):
    body = f"{account}.{int(time.time()) + int(exp)}"
    return body + "." + sign(d, body)


def id_token(d, claims):
    body = ".".join(b64(json.dumps(x).encode()) for x in ({"alg": "HS256", "typ": "JWT"}, claims))
    return body + "." + sign(d, body)


def id_account(d, tok):  # the id_token's account when its signature and expiry hold, else None
    try:
        body, mac = tok.rsplit(".", 1); claims = json.loads(base64.urlsafe_b64decode(body.split(".")[1] + "=="))
        return claims["sub"] if hmac.compare_digest(mac, sign(d, body)) and claims["exp"] > time.time() else None
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


class GameSession(http.server.BaseHTTPRequestHandler):
    dir = Path(".")  # serve's DIR
    codes, sessions = {}, {}  # code -> nonce; sessionId -> account

    def send(self, status, body=b"", ctype="application/json", location=None):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(status); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body)))
        if location:
            self.send_header("Location", location)
        self.end_headers(); self.wfile.write(body)

    def answer(self):
        u = urllib.parse.urlsplit(self.path); p, q = u.path, dict(urllib.parse.parse_qsl(u.query))
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
        iss = f"{'https' if isinstance(self.connection, ssl.SSLSocket) else 'http'}://{self.headers.get('Host')}/"
        account = lambda: (self.dir / "account").read_text().strip()
        if p.endswith("/.well-known/openid-configuration"):
            return self.send(200, {"issuer": iss, "authorization_endpoint": iss + "oauth2/auth", "token_endpoint": iss + "oauth2/token",
                                   "userinfo_endpoint": iss + "userinfo", "jwks_uri": iss + "jwks", "response_types_supported": ["code"],
                                   "subject_types_supported": ["public"], "id_token_signing_alg_values_supported": ["HS256"],
                                   "scopes_supported": ["openid", "offline", "gamesso.token.create"], "code_challenge_methods_supported": ["S256"]})
        if p.endswith("/oauth2/auth"):  # signs in at once: back to the app with a code
            if "redirect_uri" not in q:
                return self.send(400, b"missing redirect_uri", "text/plain")
            code = secrets.token_hex(16); self.codes[code] = q.get("nonce")
            state = "&state=" + urllib.parse.quote(q["state"], safe="") if "state" in q else ""
            return self.send(302, location=f"{q['redirect_uri']}?code={code}{state}", ctype="text/plain")
        if p.endswith("/oauth2/token"):
            f = dict(urllib.parse.parse_qsl(raw)); now = int(time.time())
            claims = {"iss": iss, "sub": account(), "aud": f.get("client_id", "com_jagex_auth_mobile_android_osrs"), "exp": now + 86400, "iat": now,
                      "login_provider": "jagex", "nickname": account()}
            if self.codes.get(f.get("code")):
                claims["nonce"] = self.codes[f["code"]]
            self.codes.pop(f.get("code"), None)
            return self.send(200, {"access_token": secrets.token_hex(16), "token_type": "Bearer", "expires_in": 86400, "refresh_token": secrets.token_hex(16),
                                   "id_token": id_token(self.dir, claims), "scope": "openid offline gamesso.token.create"})
        if p.endswith("/userinfo"):
            return self.send(200, {"sub": account(), "nickname": account()})
        if p.endswith("/jwks"):
            return self.send(200, {"keys": []})
        if p.endswith("game-session/v1/sessions"):
            try:
                acc = id_account(self.dir, json.loads(raw)["idToken"])
            except (ValueError, KeyError, TypeError):
                acc = None
            if not acc:
                return self.send(401, {"error": "invalid idToken"})
            sid = secrets.token_hex(16); self.sessions[sid] = acc
            return self.send(200, {"sessionId": sid})
        if p.endswith("game-session/v1/accounts"):
            acc = self.sessions.get(self.headers.get("Authorization", "").removeprefix("Bearer "))
            if not acc:
                return self.send(401, {"error": "invalid session"})
            n = zlib.crc32(acc.encode()) & 0x7FFFFFFF  # a stable number per account name
            return self.send(200, [{"accountId": n, "displayName": acc, "userHash": n}])
        if p.endswith("game-session/v1/tokens"):
            t = self.dir / "token"
            return self.send(200, {"token": t.read_text().strip() if t.exists() else mint(self.dir, account())})
        self.send_error(404)

    do_GET = do_POST = answer


def serve(d, https=8080, http_port=8081):
    GameSession.dir = Path(d)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); tls.load_cert_chain(f"{d}/tls.pem", f"{d}/tls.key")
    s = http.server.ThreadingHTTPServer(("", https), GameSession); s.socket = tls.wrap_socket(s.socket, server_side=True)
    threading.Thread(target=http.server.ThreadingHTTPServer(("", http_port), GameSession).serve_forever, daemon=True).start()
    s.serve_forever()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "key":
        print(key(a[1]))
    elif a[0] == "mint":
        print(mint(a[1], a[2], a[4] if a[3:4] == ["--exp"] else 3600))
    elif a[0] == "serve":
        serve(a[1])
