#!/usr/bin/env python3
"""Computes project progress from the code; writes docs/progress.md, docs/progress.svg (map),
the README status block and docs/progress-history.csv.

Metrics (all counted from source, nothing hand-maintained):
- Mobile protocol: opcodes named in the Android prot enums (identified) and opcodes with a real
  codec bound in AndroidRepositories.kt (implemented), against the client's own size tables
  (151 server->client, 102 client->server opcodes).
- Zone sub-prots: rows of the zone table in docs/android-protocol.md with a payload layout.
- RuneLite API: abstract methods of each interface the host backs that the Android* class
  implements (tools/progress/ApiCoverage.java; needs host/build.sh output in re/host/classes).

Usage: tools/progress.py [--no-history] [--working] [--dry-run]
  --dry-run prints the numbers and per-interface API gaps without writing any file (for agents).
  Protocol numbers come from sidecar/rsprot.patch as committed in the fork's local/server-tools; --working reads the
  sidecar/rsprot working copy instead (uncommitted work, never for published numbers).
"""
import csv
import datetime
import os
import re
import subprocess
import tempfile
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_TOOLS = os.environ.get("SERVER_TOOLS") or os.path.expanduser("~/src/openrune-work/server-tools")   # the fork's local/server-tools
RSPROT = os.path.join(SERVER_TOOLS, "sidecar/rsprot")
ANDROID = os.path.join(RSPROT, "protocol/osrs-241/osrs-241-android/src/main/kotlin/net/rsprot/protocol/android")
S2C_TOTAL, C2S_TOTAL, ZONE_TOTAL = 151, 102, 15
SDK = os.environ.get("ANDROID_SDK", "/mnt/c/Users/Alex/AppData/Local/Android/Sdk")
API_PAIRS = [
    ("Client", "AndroidClient"), ("Player", "AndroidPlayer"), ("NPC", "AndroidNPC"),
    ("WorldView", "AndroidWorldView"), ("Scene", "AndroidScene"), ("Tile", "AndroidScene$Tile"),
    ("widgets.Widget", "AndroidWidget"), ("ItemContainer", "AndroidItemContainer"),
    ("ItemComposition", "AndroidItemComposition"), ("NPCComposition", "AndroidNPCComposition"),
    ("EnumComposition", "AndroidEnum"), ("MessageNode", "AndroidMessageNode"),
    ("Menu", "AndroidMenu"), ("MenuEntry", "AndroidMenuEntry"),
]


def read(path):
    with open(path) as f:
        return f.read()


def enum_entries(src):
    return re.findall(r"^\s+([A-Z][A-Z0-9_]*)\((\d+),", src, re.M)


def placeholder(name):
    """OP_n and UNKNOWN_* entries only frame a packet; they don't identify it."""
    return bool(re.fullmatch(r"OP_\d+|UNKNOWN\w*", name))


def dead_entries(src):
    """Entries tagged `// dead: <evidence>`: no sender/handler in the client, so never on the wire."""
    return re.findall(r"^\s+([A-Z][A-Z0-9_]*)\((\d+),.*// dead", src, re.M)


def unverified_entries(src):
    """Enum entries tagged `// unverified: <reason>` (identity or layout not read from the client)."""
    return re.findall(r"^\s+([A-Z][A-Z0-9_]*)\((\d+),.*// unverified", src, re.M)


def protocol():
    s2c_src = read(os.path.join(ANDROID, "AndroidGameServerProt.kt"))
    c2s_src = read(os.path.join(ANDROID, "AndroidGameClientProt.kt"))
    s2c, c2s = enum_entries(s2c_src), enum_entries(c2s_src)
    c2s_named = [n for n, _ in c2s if not placeholder(n)]
    repo = read(os.path.join(ANDROID, "AndroidRepositories.kt"))
    enc, dec = repo.split("object AndroidGameMessageDecoderRepository")[:2]
    s2c_impl = len(re.findall(r"^\s+bind(?:WithAlts)?\(", enc, re.M))
    # Decoders are bound in several styles (bind(...), bound(...) lists, Triple tables), so count
    # named client prots referenced anywhere outside the enum and the unknown-packet fallback:
    # by the full enum name, or via a file-local `typealias X = AndroidGameClientProt`.
    named = {n for n, _ in c2s if not placeholder(n)}
    used = set()
    for f in os.listdir(ANDROID):
        if not f.endswith(".kt") or f == "AndroidGameClientProt.kt":
            continue
        src = read(os.path.join(ANDROID, f))
        aliases = ["AndroidGameClientProt"] + re.findall(r"typealias (\w+) = AndroidGameClientProt\b", src)
        for a in aliases:
            used |= set(re.findall(r"\b" + a + r"\.([A-Z][A-Z0-9_]*)\b", src))
    c2s_impl = len(named & used)
    s2c = [(n, o) for n, o in s2c if not placeholder(n)]
    return {
        "s2c_ident": len(s2c), "s2c_impl": s2c_impl,
        "dead": len(dead_entries(s2c_src)) + len(dead_entries(c2s_src)),
        "unverified": sum(1 for n, _ in unverified_entries(s2c_src) + unverified_entries(c2s_src) if not placeholder(n)),
        "c2s_ident": len(c2s_named), "c2s_impl": c2s_impl,
        "s2c_unknown": sorted(set(range(S2C_TOTAL)) - {int(o) for _, o in s2c}),
        "c2s_unknown": [int(o) for n, o in c2s if placeholder(n)],
    }


def zone():
    doc = (git("show", "HEAD:docs/android-protocol.md") if COMMITTED else read(os.path.join(ROOT, "docs/android-protocol.md")))
    doc = doc.split("## Zone packets")[1].split("\n## ")[0]
    rows = re.findall(r"^\| (\d+) \| (\w+) \|[^|]*\|([^|]*)\|", doc, re.M)
    return sum(1 for _, _, payload in rows if payload.strip()), [n for _, n, p in rows if p.strip()]


def api():
    rl = os.path.join(ROOT, "re/runelite")
    cp = ":".join([os.path.join(ROOT, "re/host/classes")] +
                  [os.path.join(rl, j) for j in sorted(os.listdir(rl)) if j.endswith(".jar")] +
                  [os.path.join(SDK, "platforms/android-37.0/android.jar")])
    args = [a for pair in API_PAIRS for a in pair]
    res = subprocess.run(["java", "-cp", cp, os.path.join(ROOT, "tools/progress/ApiCoverage.java")] + args,
                         capture_output=True, text=True)
    if res.returncode:  # e.g. host/build.sh is rewriting re/host/classes right now
        sys.exit("ApiCoverage failed (rerun after host/build.sh finishes):\n" + res.stderr[-2000:])
    out = res.stdout
    rows = []
    for line in out.splitlines():
        iface, impl, done, total, *_ = line.split()
        rows.append((iface.split(".")[-1], int(done), int(total)))
    return rows


def plugins(section="Core plugin status"):
    """Rows of the `## <section>` table in docs/plugin-host.md: (runs, starts, total)."""
    try:
        doc = read(os.path.join(ROOT, "docs/plugin-host.md"))
    except OSError:
        return 0, 0, 0
    if "## " + section not in doc:
        return 0, 0, 0
    sect = doc.split("## " + section, 1)[1].split("\n## ", 1)[0]
    st = [m.lower() for m in re.findall(r"^\|[^|\n]+\|\s*`?(runs|starts|throws|untested)`?\s*\|", sect, re.M | re.I)]
    return st.count("runs"), st.count("starts"), len(st)


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def bar(p, width=20):
    n = round(p / 100 * width)
    return "█" * n + "░" * (width - n)


GREEN, AMBER, GREY, BG, FG = "#2ea043", "#d29922", "#6e7681", "#0d1117", "#ffffff"


def squarify(sizes, x, y, w, h):
    """Squarified treemap: returns one (x, y, w, h) per size (sizes sorted descending)."""
    out, sizes = [], [s * w * h / sum(sizes) for s in sizes]
    while sizes:
        short = min(w, h)
        row = [sizes[0]]

        def worst(r):
            s = sum(r)
            return max(max(short * short * v / (s * s), s * s / (short * short * v)) for v in r)

        i = 1
        while i < len(sizes) and worst(row + [sizes[i]]) <= worst(row):
            row.append(sizes[i])
            i += 1
        sizes = sizes[i:]
        s = sum(row)
        if w >= h:  # lay the row out as a column on the left
            cw, cy = s / h, y
            for v in row:
                out.append((x, cy, cw, v / cw))
                cy += v / cw
            x, w = x + cw, w - cw
        else:  # as a row on top
            rh, cx = s / w, x
            for v in row:
                out.append((cx, y, v / rh, rh))
                cx += v / rh
            y, h = y + rh, h - rh
    return out


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_section(groups, x, y, w, h):
    """groups: (label, title, [colour per cell]); boxes sized by cell count, cells in a grid."""
    groups = sorted(groups, key=lambda g: -len(g[2]))
    parts = []
    for (label, title, cells), (gx, gy, gw, gh) in zip(groups, squarify([len(g[2]) for g in groups], x, y, w, h)):
        n = len(cells)
        cols = max(1, min(n, round((n * gw / gh) ** 0.5)))
        rows = -(-n // cols)
        cw, ch = (gw - 2) / cols, (gh - 2) / rows
        parts.append(f"<g><title>{esc(title)}</title>")
        for i, colour in enumerate(cells):
            r, c = divmod(i, cols)
            parts.append(f'<rect x="{gx + 1 + c * cw:.2f}" y="{gy + 1 + r * ch:.2f}" width="{cw:.2f}" height="{ch:.2f}" '
                         f'fill="{colour}" stroke="{BG}" stroke-width="0.5"/>')
        parts.append(f'<rect x="{gx:.2f}" y="{gy:.2f}" width="{gw:.2f}" height="{gh:.2f}" fill="none" stroke="{BG}" stroke-width="2"/>')
        if gw > 7 * len(label) + 8 and gh > 18:
            parts.append(f'<text x="{gx + 5:.2f}" y="{gy + 16:.2f}" font-family="sans-serif" font-size="12" fill="{FG}" '
                         f'stroke="{BG}" stroke-width="3" paint-order="stroke">{esc(label)}</text>')
        parts.append("</g>")
    return parts


def heading(text, y):
    return f'<text x="4" y="{y}" font-family="sans-serif" font-size="16" fill="{FG}">{esc(text)}</text>'


def write_svg(path, p, z_done, rows):
    def cells(impl, mapped, total):
        return [GREEN] * impl + [AMBER] * (mapped - impl) + [GREY] * (total - mapped)

    W = 1000
    ident, impl, total = p["s2c_ident"] + p["c2s_ident"], p["s2c_impl"] + p["c2s_impl"], S2C_TOTAL + C2S_TOTAL
    packets = [
        ("Server→client", f"Server→client: {p['s2c_ident']}/{S2C_TOTAL} mapped, {p['s2c_impl']} implemented",
         cells(p["s2c_impl"], p["s2c_ident"], S2C_TOTAL)),
        ("Client→server", f"Client→server: {p['c2s_ident']}/{C2S_TOTAL} mapped, {p['c2s_impl']} implemented",
         cells(p["c2s_impl"], p["c2s_ident"], C2S_TOTAL)),
        ("Zone", f"Zone sub-prots: {z_done}/{ZONE_TOTAL} implemented", cells(z_done, z_done, ZONE_TOTAL)),
    ]
    api_done, api_total = sum(r[1] for r in rows), sum(r[2] for r in rows)
    api_groups = [(iface, f"{iface}: {a}/{b} ({pct(a, b):.0f}%)", cells(a, a, b)) for iface, a, b in rows]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 470" width="{W}" height="470">',
           f'<rect x="0" y="0" width="{W}" height="470" fill="{BG}"/>',
           heading(f"Mobile packets: {pct(ident, total):.2f}% mapped ({ident}/{total}), "
                   f"{pct(impl, total):.2f}% implemented ({impl}); {p['unverified']} mapped entries unverified", 21)]
    out += svg_section(packets, 1, 31, W - 2, 150)
    out.append(heading(f"RuneLite API*: {pct(api_done, api_total):.2f}% ({api_done}/{api_total})", 210))
    out += svg_section(api_groups, 1, 220, W - 2, 230)
    legend = [(GREEN, "implemented"), (AMBER, "mapped, not implemented"), (GREY, "unknown / missing")]
    lx = 4
    for colour, text in legend:
        out.append(f'<rect x="{lx}" y="457" width="10" height="10" fill="{colour}"/>')
        out.append(f'<text x="{lx + 14}" y="466" font-family="sans-serif" font-size="11" fill="{FG}">{text}</text>')
        lx += 30 + 6 * len(text)
    out.append("</svg>")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")


def git(*args):
    return subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True).stdout.strip()


COMMITTED = False


def use_committed_protocol():
    """Point ANDROID at the Android module as committed (sidecar/rsprot.patch in local/server-tools), so the
    published numbers never include another agent's uncommitted work."""
    global ANDROID, COMMITTED
    COMMITTED = True
    tmp = tempfile.mkdtemp(prefix="progress-rsprot-")
    patch = subprocess.run(["git", "-C", SERVER_TOOLS, "show", "HEAD:sidecar/rsprot.patch"], capture_output=True, check=True).stdout
    subprocess.run(["git", "apply", "--include=protocol/osrs-241/osrs-241-android/*", "-"], cwd=tmp, input=patch, check=True)
    ANDROID = os.path.join(tmp, os.path.relpath(ANDROID, RSPROT))


def main():
    if "--working" not in sys.argv:
        use_committed_protocol()
    p = protocol()
    z_done, z_names = zone()
    rows = api()
    api_done, api_total = sum(r[1] for r in rows), sum(r[2] for r in rows)
    ident = p["s2c_ident"] + p["c2s_ident"]
    impl = p["s2c_impl"] + p["c2s_impl"]
    total = S2C_TOTAL + C2S_TOTAL
    commit = git("rev-parse", "--short", "HEAD")
    dirty = "+" if git("status", "--porcelain", "--untracked-files=no") else ""
    today = datetime.date.today().isoformat()

    head = [
        ("Mobile packets mapped", ident, total, "named opcodes, both directions, of the client's size tables"),
        ("Live packets mapped", ident, total - p["dead"],
         "mapped of the opcodes the client can actually send/handle (entries tagged `// dead: evidence` excluded)"),
        ("Mobile packets mapped, verified", ident - p["unverified"], total,
         "mapped minus entries tagged `// unverified` (identity/layout not read from the client code)"),
        ("Mobile packets implemented", impl, total, "opcodes with an Android codec bound on the server"),
        ("Server→client mapped", p["s2c_ident"], S2C_TOTAL, "AndroidGameServerProt"),
        ("Client→server mapped", p["c2s_ident"], C2S_TOTAL, "AndroidGameClientProt (not OP_n / UNKNOWN_*)"),
        ("Zone sub-prots implemented", z_done, ZONE_TOTAL, ", ".join(z_names)),
        ("RuneLite API implemented", api_done, api_total, "abstract methods of the interfaces below"),
    ]
    p_runs, p_starts, p_total = plugins()
    if p_total:
        head.append(("Plugins running on Android", p_runs, p_total,
                     f"rows marked `runs` in docs/plugin-host.md's Core plugin status table ({p_starts} more start)"))
    h_runs, h_starts, h_total = plugins("Plugin Hub status")
    if h_total:
        head.append(("Plugin Hub plugins running", h_runs, h_total,
                     f"rows marked `runs` in docs/plugin-host.md's Plugin Hub status table ({h_starts} more start)"))
    md = [
        "# Progress",
        "",
        f"Generated by `tools/progress.py` on {today} at `{commit}{dirty}`. Do not edit by hand;",
        "history is in [`progress-history.csv`](progress-history.csv). Percentages are of what the",
        "project can enumerate: the Android client's own opcode size tables, and the RuneLite API",
        "interfaces the plugin host backs (new interfaces raise the denominator, like AnyPS5's",
        "\"functions known to the project\").",
        "",
        "| Metric | Done | Total | % | |",
        "|---|---:|---:|---:|---|",
    ]
    for name, a, b, note in head:
        md.append(f"| **{name}** | {a} | {b} | {pct(a, b):.1f}% | `{bar(pct(a, b))}` |")
    md += ["", "Notes: " + "; ".join(f"*{n}*: {note}" for n, _, _, note in head), ""]
    md += ["## RuneLite API by interface", "", "| Interface | Implemented | Total | % |", "|---|---:|---:|---:|"]
    for iface, a, b in sorted(rows, key=lambda r: -pct(r[1], r[2])):
        md.append(f"| `{iface}` | {a} | {b} | {pct(a, b):.0f}% |")
    if "--dry-run" in sys.argv:
        for name, a, b, _ in head:
            print(f"{name:28} {a:4}/{b:<4} {pct(a, b):5.1f}%")
        for iface, a, b in sorted(rows, key=lambda r: r[1] - r[2]):
            if a < b:
                print(f"  {iface:28} {a:4}/{b:<4} missing {b - a}")
        return
    md += ["", "## Unmapped opcodes", "",
           f"- Client→server ({len(p['c2s_unknown'])}): " + ", ".join(map(str, p["c2s_unknown"])),
           f"- Server→client ({len(p['s2c_unknown'])}): " + ", ".join(map(str, p["s2c_unknown"])),
           "",
           "Some server→client opcodes are recognised in `docs/android-protocol.md` but not yet in the",
           "enum; they count once added there.", ""]
    with open(os.path.join(ROOT, "docs/progress.md"), "w") as f:
        f.write("\n".join(md))

    write_svg(os.path.join(ROOT, "docs/progress.svg"), p, z_done, rows)

    readme = os.path.join(ROOT, "README.md")
    if os.path.exists(readme):
        text = read(readme)
        badges = " ".join(
            f"![{n}](https://img.shields.io/badge/{n.replace(' ', '%20').replace('→', '%E2%86%92')}-{pct(a, b):.1f}%25-blue)"
            for n, a, b, _ in head if n in ("Mobile packets mapped", "Mobile packets implemented", "RuneLite API implemented", "Plugins running on Android", "Plugin Hub plugins running"))
        block = (f"<!-- progress:start -->\n{badges}\n\n[![Progress map](docs/progress.svg)](docs/progress.md)\n\n"
                 + "\n".join(f"- **{n}**: {a}/{b} ({pct(a, b):.1f}%)" for n, a, b, _ in head)
                 + "\n\n\\* RuneLite API: abstract methods of the API interfaces the plugin host backs so far, not of the"
                 " whole RuneLite API. Mobile packets count the opcodes in the client's own size tables."
                 + f"\n\nDetails: [docs/progress.md](docs/progress.md) (as of {today}, `{commit}{dirty}`).\n<!-- progress:end -->")
        text = re.sub(r"<!-- progress:start -->.*?<!-- progress:end -->", lambda _: block, text, flags=re.S)
        with open(readme, "w") as f:
            f.write(text)

    if "--no-history" not in sys.argv:
        path = os.path.join(ROOT, "docs/progress-history.csv")
        fields = ["date", "commit", "packets_mapped", "packets_implemented", "s2c_mapped", "c2s_mapped",
                  "zone_impl", "api_impl", "api_total", "packets_total"]
        hist = list(csv.DictReader(open(path))) if os.path.exists(path) else []
        hist = [h for h in hist if h["date"] != today]  # one row per day, latest wins
        hist.append(dict(zip(fields, [today, commit + dirty, ident, impl, p["s2c_ident"], p["c2s_ident"],
                                      z_done, api_done, api_total, total])))
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(hist)

    for name, a, b, _ in head:
        print(f"{name:28} {a:4}/{b:<4} {pct(a, b):5.1f}%")


if __name__ == "__main__":
    main()
