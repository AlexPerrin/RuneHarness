#!/usr/bin/env python3
"""issuer.py key DIR: the key of the test and live stacks' sign-in (embedded Central's). Makes DIR/secret (Central's
OPENRUNE_SIGN_IN_TOKEN_SECRET, with which it signs the compact <account>.<expiry>.<HMAC-SHA256> token the game verifies) and
DIR/tls.pem with tls.key (the certificate Central serves https with, which every desktop trusts) once; prints the game.yml
token-login block holding the secret.
"""
import base64, datetime, ipaddress, os, sys
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pathlib import Path


def key(d):
    d = Path(d); d.mkdir(parents=True, exist_ok=True); sec = d / "secret"
    if not sec.exists():
        sec.write_text(base64.b64encode(os.urandom(32)).decode())
    if not (d / "tls.pem").exists():
        k = rsa.generate_private_key(public_exponent=65537, key_size=2048); now = datetime.datetime.now(datetime.timezone.utc)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(k.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - datetime.timedelta(days=1))   # a WSL clock stepped back mid-gate must not make it "not yet valid" (openssl 3.0 req cannot backdate)
                .not_valid_after(now + datetime.timedelta(days=3650))
                .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
                .sign(k, hashes.SHA256()))
        (d / "tls.key").write_bytes(k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        (d / "tls.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return f'token-login:\n  secret: "{sec.read_text()}"'


if __name__ == "__main__":
    print(key(sys.argv[2]))
