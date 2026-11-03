"""tools/docfmt.py [--check] <doc>...: the source docs hold one fact per line, so sibling changes merge and only the same fact
changed two ways conflicts (R8). Prose splits after '; ' and each sentence end, a table becomes one block per row, a file-tree
entry in a code block splits at '; '; the loop block and fenced blocks with a language stay as written.
--check rewrites nothing and fails naming each doc the format would change."""
import re, sys
SPLIT = re.compile(r"(?<=;) (?=\S)|(?<!e\.g\.)(?<=[a-zA-Z)`'\"]\.) (?=[A-Z`*(])")
def facts(text): return [p for p in SPLIT.split(text) if p]
def cells(l): return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", l.strip()[1:-1])]

def table(rows, kind):
    out = []
    head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
    if kind == "req":   # | R1 **Goals** | constraint | P1 P10 |
        for r in body:
            out += ["", f"### {r[0].replace('**', '')}" + (f" (from {r[2]})" if len(r) > 2 else ""), *facts(r[1])]
    elif kind == "cmd":  # | cmd | who | does |
        for r in body:
            f = facts(r[2])
            out += ["", f"- {r[0]}, by {r[1]}: {f[0]}", *["  " + x for x in f[1:]]]
    elif kind == "tracks":  # | | Client | Server | Central | Harness |
        for r in body:
            out += ["", f"**{r[0]}**"]
            for t, c in zip(head[1:], r[1:]):
                f = facts(c)
                out += [f"- {t}: {f[0]}", *["  " + x for x in f[1:]]]
    elif kind == "rows":  # | Track | Delivers | Goal |: a block per row, a line per column
        for r in body:
            out += ["", f"### {r[0]}", *[f"- {h}: {x}" if k == 0 else "  " + x for h, c in zip(head[1:], r[1:]) for k, x in enumerate(facts(c))]]
    elif kind == "mech":
        for r in body:
            out += ["", f"- {r[0]}: {r[1]}"]
    return out[1:]

def kind(h):
    c = cells(h)
    return {"Id": "req", "Command": "cmd", "": "tracks", "Requirement": "mech", "Track": "rows"}.get(c[0])

def code_entries(lines):
    """A file-tree or data block: an entry starts at column 0, its continuation lines are indented to the text column."""
    out, i = [], 0
    while i < len(lines):
        l = lines[i]; m = re.match(r"(\S+\s{2,})(.*)", l)
        if not m or l.startswith("~") or l.startswith("python3") or l.startswith("loginctl") or l.startswith("fork ") or l.startswith("each "):
            out.append(l); i += 1; continue
        col, text = len(m[1]), m[2]
        j = i + 1
        while j < len(lines) and lines[j].startswith(" " * col) and lines[j].strip():
            text += " " + lines[j].strip(); j += 1
        f = facts(text) if len(text) > 120 or j > i + 1 else [text]
        out += [m[1] + f[0], *[" " * col + x for x in f[1:]]]
        i = j
    return out

def fmt(src, loop_marker="next(change):"):
    L, out, i = src.split("\n"), [], 0
    while i < len(L):
        l = L[i]
        if l.startswith("```"):
            j = i + 1
            while not L[j].startswith("```"): j += 1
            body = L[i + 1:j]
            if l == "```" and body and not body[0].startswith(loop_marker) and not body[0].startswith("~"):
                body = code_entries(body)
            out += [l, *body, L[j]]; i = j + 1; continue
        if l.startswith("|"):
            j = i
            while j < len(L) and L[j].startswith("|"): j += 1
            k = kind(L[i])
            out += table(L[i:j], k) if k else L[i:j]; i = j; continue
        if not l.strip() or l.startswith("#"):
            out.append(l); i += 1; continue
        m = re.match(r"(\d+\. |- |\s*)", l); ind = " " * len(m[1]); text = l
        j = i + 1
        while j < len(L) and L[j].strip() and not L[j].startswith(("```", "|", "#")) and not re.match(r"\d+\. |- ", L[j]):
            text += " " + L[j].strip(); j += 1
        f = facts(text)
        out += [f[0], *[ind + x for x in f[1:]]]
        if j < len(L) and re.match(r"\d+\. ", L[j]) and re.match(r"\d+\. ", l): out.append("")
        i = j
    return "\n".join(out)

if __name__ == "__main__":
    check = sys.argv[1:2] == ["--check"]
    bad = []
    for p in sys.argv[1 + check:]:
        t = open(p).read(); f = fmt(t)
        if check and f != t:
            line = next(i for i, (a, b) in enumerate(zip(t.split("\n") + [""], f.split("\n") + [""])) if a != b) + 1
            bad.append(f"{p}:{line}: not one fact per line (tools/docfmt.py {p} rewrites it)")
        elif not check:
            open(p, "w").write(f)
    sys.exit("\n".join(bad) or None)
