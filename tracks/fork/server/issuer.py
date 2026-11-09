#!/usr/bin/env python3
"""issuer.py key DIR: the key of the test and live stacks' sign-in (embedded Central's). Makes DIR/secret (Central's
OPENRUNE_SIGN_IN_TOKEN_SECRET, with which it signs the compact <account>.<expiry>.<HMAC-SHA256> token the game verifies) and
DIR/tls.pem with tls.key (the certificate Central serves https with, which every desktop trusts) once; prints the game.yml
token-login block holding the secret.
"""
import base64, os, subprocess, sys
from pathlib import Path


def key(d):
    d = Path(d); d.mkdir(parents=True, exist_ok=True); sec = d / "secret"
    if not sec.exists():
        sec.write_text(base64.b64encode(os.urandom(32)).decode())
    if not (d / "tls.pem").exists():
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "3650", "-subj", "/CN=127.0.0.1", "-addext",
                        "subjectAltName=IP:127.0.0.1", "-keyout", str(d / "tls.key"), "-out", str(d / "tls.pem")], check=True, capture_output=True)
    return f'token-login:\n  secret: "{sec.read_text()}"'


if __name__ == "__main__":
    print(key(sys.argv[2]))
