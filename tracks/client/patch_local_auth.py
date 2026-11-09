#!/usr/bin/env python3
"""Lets the Android app sign in against the test server's local OpenID provider (LOCAL_AUTH).

Operates on a fully decoded base APK (apktool d without -r):
  * network_security_config: allow cleartext HTTP (the server speaks plain HTTP),
  * AppAuth connection builder: drop the "only https connections are permitted" precondition,
  * AppAuth ID-token validation: drop the "Issuer must be an https URL" check.
Targets are found by their strings, not by (obfuscated) class names.

Usage: patch_local_auth.py DECODED_BASE_DIR
"""
import pathlib
import re
import sys


def find_smali(root: pathlib.Path, needle: str) -> pathlib.Path:
    hits = [p for p in root.glob("smali*/**/*.smali") if needle in p.read_text(errors="ignore")]
    if len(hits) != 1:
        sys.exit(f"expected one smali file containing {needle!r}, found {len(hits)}")
    return hits[0]


def main() -> None:
    root = pathlib.Path(sys.argv[1])

    nsc = root / "res/xml/network_security_config.xml"
    text = nsc.read_text()
    if "cleartextTrafficPermitted" not in text:
        text, n = re.subn(r"<base-config>", '<base-config cleartextTrafficPermitted="true">', text)
        if n != 1:
            sys.exit("base-config not found in network_security_config.xml")
        nsc.write_text(text)
    print("patched", nsc)

    builder = find_smali(root, '"only https connections are permitted"')
    text = builder.read_text()
    text, n = re.subn(
        r'(const-string (v\d+), "only https connections are permitted"\n(?:[ \t]*\.line \d+\n|[ \t]*\n)*)'
        r"[ \t]*invoke-static \{v\d+, \2\}, L[\w/$]+;->a\(ZLjava/lang/Object;\)V\n",
        r"\1",
        text,
    )
    if n != 1:
        sys.exit(f"https precondition not found in {builder}")
    builder.write_text(text)
    print("patched", builder)

    idtoken = find_smali(root, '"Issuer must be an https URL"')
    text = idtoken.read_text()
    text, n = re.subn(
        r'(const-string (v\d+), "https"\n(?:[ \t]*\.line \d+\n|[ \t]*\n)*'
        r"[ \t]*invoke-virtual \{(v\d+), \2\}, Ljava/lang/String;->equals\(Ljava/lang/Object;\)Z\n"
        r"(?:[ \t]*\.line \d+\n|[ \t]*\n)*[ \t]*move-result (v\d+)\n(?:[ \t]*\.line \d+\n|[ \t]*\n)*)"
        r"[ \t]*if-eqz \4, :cond_\w+\n",
        r"\1",
        text,
    )
    if n != 1:
        sys.exit(f"issuer https check not found in {idtoken}")
    idtoken.write_text(text)
    print("patched", idtoken)


if __name__ == "__main__":
    main()
