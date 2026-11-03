#!/usr/bin/env python3
"""Custom gameval ids, unique across everything that goes live together: upstream main, the permanent pins and every
open dev head.
  gamevals.py check [<ref>]      ids of <ref> (default $TCOMMIT) that another member holds under another name; exit 1 if any.
                                 Upstream main never renumbers; between two of ours the earlier taker keeps the id.
  gamevals.py assign <worktree>  every `name = -1` in <worktree> gets the highest id free in every member.
Env: CLONE (the fork clone, remotes origin = upstream and fork), HD_ROOT (the harness: its hd.yaml `pins`), SLUG.
The pins are read from hd.yaml, so a hand-run assign and the gate's check see one member list.
The official ids are the cache's (.data/gamevals-binary/max-ids.toml); every id above a table's max is ours.
"""
import os, re, subprocess, sys
import yaml
from collections import defaultdict

SECTION = re.compile(r"^\s*\[gamevals\.([^.\]]+)\]\s*$")
KV = re.compile(r"^(\s*)([^=#\[]+?)(\s*=\s*)(-?\d+)(\s*)$")
TOP = {"area": 32766}  # the server keeps area ids in a short
MAX = 65535
CLONE = os.environ.get("CLONE") or os.path.expanduser("~/src/OpenRune-Server")


def git(*a):
    return subprocess.run(["git", "-C", CLONE, *a], capture_output=True, text=True).stdout


def files(ref):
    return [p for p in git("ls-tree", "-r", "--name-only", ref).split()
            if (p.endswith("/gamevals.toml") and p.startswith(("content/", "api/")) and not {"build", "out", "target"} & set(p.lower().split("/")))
            or (p.startswith(".data/gamevals/") and p.endswith(".rscm"))]


def entries(text, path):
    """(table, name, id) per gameval line; a .rscm file is one table named by the file."""
    table = os.path.basename(path)[:-5] if path.endswith(".rscm") else None
    for line in text.splitlines():
        if (s := SECTION.match(line)):
            table = None if s.group(1) == "dbcol" else s.group(1)
            continue
        if table and (m := KV.match(line.strip() if path.endswith(".rscm") else line)):
            yield table, m.group(2).strip(), int(m.group(4))


def parse_max(text):
    text = text.split("[max_ids]", 1)[-1]
    return {k.strip(): int(v) for k, v in (l.split("=", 1) for l in text.splitlines() if "=" in l and not l.strip().startswith("#"))}


def maxes(ref):
    mx = parse_max(git("show", f"{ref}:.data/gamevals-binary/max-ids.toml"))
    if not mx:
        sys.exit(f"max-ids.toml missing at {ref[:9]}")
    return mx


def ids(ref, mx):
    """{(table, id): name} of the ids at <ref> above the given maxes."""
    return {(t, i): n for p in files(ref) for t, n, i in entries(git("show", f"{ref}:{p}"), p) if i > mx.get(t, -1)}


def members():
    own = f"dev/{os.environ.get('SLUG', '')}"
    cfg = os.path.join(os.environ.get("HD_ROOT") or os.path.expanduser("~/osrs-harness"), "hd.yaml")
    out = [("upstream main", "origin/main")] + [(p, f"fork/{p}") for p in yaml.safe_load(open(cfg)).get("pins") or []]
    for r in git("for-each-ref", "--format=%(refname:short)", "refs/remotes/fork/dev/").split():
        b = r[len("fork/"):]
        if b != own and subprocess.run(["git", "-C", CLONE, "merge-base", "--is-ancestor", r, "origin/main"]).returncode:
            out.append((b, r))
    return out


def first(ref, name, i):
    ts = git("log", "--format=%ct", "-G", rf"^\s*{re.escape(name)}\s*=\s*{i}\s*$", ref, "--").split()
    return int(ts[-1]) if ts else 0


def check(ref):
    mx = maxes(ref)
    mine = ids(ref, mx)
    bad = [f"area.{n} = {i} is past the server's area limit {TOP['area']}" for (t, i), n in mine.items() if t == "area" and i > TOP["area"]]
    main = ids("origin/main", mx)
    mine = {k: n for k, n in mine.items() if main.get(k) != n}
    for label, r in members():
        for (t, i), n in ids(r, mx).items():
            if (t, i) in mine and mine[(t, i)] != n and (label == "upstream main" or (first(r, n, i), n) < (first(ref, mine[(t, i)], i), mine[(t, i)])):
                bad.append(f"{t}.{mine[(t, i)]} = {i} is {t}.{n} on {label}, which had it first: renumber (name = -1, then gamevals.py assign)")
    print("\n".join(bad) or f"gameval ids at {ref[:9]}: unique across upstream main, the pins and the open dev heads")
    return 1 if bad else 0


def assign(tree):
    taken = defaultdict(set)
    mx = parse_max(open(os.path.join(tree, ".data/gamevals-binary/max-ids.toml")).read())
    for _, r in members():
        for t, i in ids(r, mx):
            taken[t].add(i)
    paths = [os.path.join(d, f) for base in ("content", "api") for d, _, fs in os.walk(os.path.join(tree, base))
             if not {"build", "out", "target"} & set(d.lower().split(os.sep)) for f in fs if f == "gamevals.toml"]
    gv = os.path.join(tree, ".data", "gamevals")
    paths += [os.path.join(gv, f) for f in sorted(os.listdir(gv)) if f.endswith(".rscm")] if os.path.isdir(gv) else []
    for p in paths:
        for t, _, i in entries(open(p).read(), p):
            taken[t].add(i)
    for p in paths:
        lines, table, changed = open(p).read().split("\n"), os.path.basename(p)[:-5] if p.endswith(".rscm") else None, False
        for k, line in enumerate(lines):
            if (s := SECTION.match(line)):
                table = None if s.group(1) == "dbcol" else s.group(1)
                continue
            if table and (m := KV.match(line.strip() if p.endswith(".rscm") else line)) and m.group(4) == "-1":
                new = next(i for i in range(TOP.get(table, MAX), mx.get(table, -1), -1) if i not in taken[table])
                taken[table].add(new)
                lines[k] = re.sub(r"-1(\s*)$", rf"{new}\1", line)
                changed = True
                print(f"{table}.{m.group(2).strip()} = {new}")
        if changed:
            open(p, "w").write("\n".join(lines))


if __name__ == "__main__":
    ref = sys.argv[2] if len(sys.argv) > 2 else os.environ.get("TCOMMIT")
    if len(sys.argv) < 2 or sys.argv[1] not in ("check", "assign") or not ref:
        sys.exit("usage: gamevals.py check [<ref>] | assign <worktree>   (check needs a ref or $TCOMMIT)")
    sys.exit(check(ref) if sys.argv[1] == "check" else assign(ref))
