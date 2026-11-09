#!/usr/bin/env python3
"""Turns off the official app's third-party telemetry in a fully decoded base APK (docs/app-telemetry.md).

  A. Singular never starts: the static starter of the app's Singular wrapper (sa.b.a(Activity, String,
     String) in 241.4, found as the static (Activity, String, String) method that does `new-instance` of
     the class holding the "Singular Initialized" log string) returns at once. The wrapper's other entry
     points already null-check the instance, and the consent callback that calls it still runs its
     continuation.
  C. AndroidManifest meta-data firebase_analytics_collection_deactivated=true (Firebase's permanent
     switch; it overrides the app's runtime setAnalyticsCollectionEnabled(true)).
  D. AndroidManifest meta-data firebase_crashlytics_collection_enabled=false.

  E. The consent sync never reaches Jagex (docs/app-telemetry.md): the CMP flow's consent POST client
     (za.l.a(url, token, body) in 241.4, found as the (String, String, String) method that starts the
     AsyncTask holding "Consent sync failed with HTTP ") returns at once, and, with --native, the game
     library's sync URLs (account.jagex.com and the dev account.development.jxp.jagex.com) are zeroed,
     so the SDK takes its "sync client is not configured" path (za.f.b: blank or whitespace-only URL;
     NUL is whitespace to String.trim()). The group-ironman score URL (pp-%s.%s.jagex.com:13406, native
     FUN_0064da14 Ghidra) gets the reserved host suffix x.invalid instead of jagex.com (same length), and
     the web URL builder's bare "runescape.com" (secure./services. URLs, FUN_0051102c Ghidra) becomes
     "x.invalid" plus NUL padding.

Idempotent on the decoded APK: a patched method carries a marker comment, and meta-data are set rather
than duplicated. --native works on a freshly extracted library (it fails if the URLs aren't there).

Usage: patch_telemetry.py DECODED_BASE_DIR
       patch_telemetry.py --native IN_SO OUT_SO
"""
import pathlib
import re
import sys

MARKER = "# osrsrl: telemetry off (tools/patch_telemetry.py)"
META = {
    "firebase_analytics_collection_deactivated": "true",
    "firebase_crashlytics_collection_enabled": "false",
}


def patch_singular(root: pathlib.Path) -> None:
    holders = [p for p in root.glob("smali*/**/*.smali") if '"Singular Initialized"' in p.read_text(errors="ignore")]
    if len(holders) != 1:
        sys.exit(f"telemetry: expected one smali file with \"Singular Initialized\", found {len(holders)}")
    cls = re.search(r"^\.class [^\n]*?(L[^;\s]+;)", holders[0].read_text(), re.M).group(1)
    sig = ".method public static a(Landroid/app/Activity;Ljava/lang/String;Ljava/lang/String;)V"
    method = re.compile(r"(\.method public static \w+\(Landroid/app/Activity;Ljava/lang/String;Ljava/lang/String;\)V\n)(.*?)(\.end method)", re.S)
    done = 0
    for p in root.glob("smali*/**/*.smali"):
        text = p.read_text(errors="ignore")
        if MARKER not in text and ("new-instance" not in text or cls not in text):
            continue
        def repl(m):
            nonlocal done
            body = m.group(2)
            if MARKER in body:
                done += 1
                return m.group(0)
            if not re.search(r"new-instance [vp]\d+, " + re.escape(cls), body):
                return m.group(0)
            done += 1
            return m.group(1) + f"    .locals 0\n\n    {MARKER}\n    return-void\n" + m.group(3)
        new = method.sub(repl, text)
        if new != text:
            p.write_text(new)
            print("telemetry: Singular starter disabled in", p.relative_to(root))
    if done != 1:
        sys.exit(f"telemetry: expected one Singular starter ({sig} creating {cls}), found {done}")


def patch_consent_sync(root: pathlib.Path) -> None:
    holders = [p for p in root.glob("smali*/**/*.smali") if '"Consent sync failed with HTTP "' in p.read_text(errors="ignore")]
    if len(holders) != 1:
        sys.exit(f"telemetry: expected one smali file with the consent sync failure string, found {len(holders)}")
    task = re.search(r"^\.class [^\n]*?(L[^;\s]+;)", holders[0].read_text(), re.M).group(1)
    method = re.compile(r"(\.method (?:public |final |private )*\w+\(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;\)V\n)(.*?)(\.end method)", re.S)
    done = 0
    for p in root.glob("smali*/**/*.smali"):
        if p == holders[0]:
            continue
        text = p.read_text(errors="ignore")
        if MARKER not in text and task not in text:
            continue
        def repl(m):
            nonlocal done
            body = m.group(2)
            if MARKER in body:
                done += 1
                return m.group(0)
            if not re.search(r"new-instance [vp]\d+, " + re.escape(task), body):
                return m.group(0)
            done += 1
            return m.group(1) + f"    .locals 0\n\n    {MARKER}\n    return-void\n" + m.group(3)
        new = method.sub(repl, text)
        if new != text:
            p.write_text(new)
            print("telemetry: consent sync POST disabled in", p.relative_to(root))
    if done != 1:
        sys.exit(f"telemetry: expected one consent sync starter (creating {task}), found {done}")


SYNC_URLS = [b"https://account.jagex.com/consent/sync", b"https://account.development.jxp.jagex.com/consent/sync"]


def patch_native(src: str, dst: str) -> None:
    data = bytearray(open(src, "rb").read())
    for url in SYNC_URLS:
        needle = b"\0" + url + b"\0"
        n = 0
        i = data.find(needle)
        while i >= 0:
            data[i + 1:i + 1 + len(url)] = bytes(len(url))
            n += 1
            i = data.find(needle, i + 1)
        if n == 0:
            sys.exit(f"telemetry: {url.decode()} not found in {src}")
        print(f"telemetry: zeroed {url.decode()} ({n}x)")
    # Group-ironman score lookups: keep the format string (and its %s count) intact but move the host
    # to the reserved .invalid TLD (RFC 2606), so the request fails like any offline lookup.
    gim_old = b"https://pp-%s.%s.jagex.com:13406/v1/groupScoreDetails/byGroupName/%s\0"
    gim_new = b"https://pp-%s.%s.x.invalid:13406/v1/groupScoreDetails/byGroupName/%s\0"
    assert len(gim_old) == len(gim_new)
    full_old, full_new = b"\0" + gim_old, b"\0" + gim_new
    n_old, n_new = data.count(full_old), data.count(full_new)
    if n_old == 1 and n_new == 0:
        i = data.find(full_old)
        data[i:i + len(full_new)] = full_new
        print("telemetry: group score host -> pp-%s.%s.x.invalid")
    elif not (n_old == 0 and n_new == 1):
        sys.exit(f"telemetry: expected exactly one group score URL in {src} (found {n_old} original, {n_new} patched)")
    # Jagex web URL builder (Ghidra FUN_0051102c, ELF 0x41102c): "%s%s%s.%s/l=%s/a=%i%s/" with the bare
    # domain "runescape.com" (its only reference, a %s argument read up to the NUL). It builds
    # https://secure.runescape.com/... (startup base URL, account-creation link) and
    # http://services.runescape.com/m=accountappeal/login.ws (native GET). Same reserved .invalid TLD,
    # padded with NULs to the original length.
    dom_old = b"\0runescape.com\0"
    dom_new = b"\0x.invalid" + bytes(len(dom_old) - len(b"\0x.invalid"))
    n_old, n_new = data.count(dom_old), data.count(dom_new)
    if n_old == 1 and n_new == 0:
        i = data.find(dom_old)
        data[i:i + len(dom_new)] = dom_new
        print("telemetry: web URL domain runescape.com -> x.invalid")
    elif not (n_old == 0 and n_new == 1):
        sys.exit(f"telemetry: expected exactly one bare runescape.com in {src} (found {n_old} original, {n_new} patched)")
    open(dst, "wb").write(data)


def patch_manifest(root: pathlib.Path) -> None:
    mf = root / "AndroidManifest.xml"
    text = mf.read_text()
    if not text.lstrip().startswith("<"):
        sys.exit("telemetry: AndroidManifest.xml is not decoded (apktool d without -r needed)")
    for name, value in META.items():
        pat = re.compile(r'<meta-data android:name="' + re.escape(name) + r'" android:value="[^"]*"\s*/>')
        line = f'<meta-data android:name="{name}" android:value="{value}"/>'
        if pat.search(text):
            text = pat.sub(line, text)
        else:
            text, n = re.subn(r"(<application\b[^>]*>)", r"\1\n        " + line, text, count=1)
            if n != 1:
                sys.exit("telemetry: <application> not found in the manifest")
    mf.write_text(text)
    print("telemetry: manifest", ", ".join(f"{k}={v}" for k, v in META.items()))


def main() -> None:
    if sys.argv[1] == "--native":
        patch_native(sys.argv[2], sys.argv[3])
        return
    root = pathlib.Path(sys.argv[1])
    patch_singular(root)
    patch_consent_sync(root)
    patch_manifest(root)


if __name__ == "__main__":
    main()
