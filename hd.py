#!/usr/bin/env python3
"""hd: the v8 harness. One loop over five nouns: change, tree T, judgment, target, run (docs/ARCHITECTURE.md).

Commands: hd | new | show | handover | verdict | ask | answer | approve | tick [--dry-run].
Every read of the world goes through Facts (tests replace it); every decision is nxt(ctx, change).
Implemented: R3 (contract, records bound to T or head + contract, refusals). The other requirements follow one at a time.
"""
import fcntl, hashlib, json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(os.environ.get("HD_ROOT") or Path(__file__).resolve().parent)
STATE, EVID, DEFS = ROOT / "state", ROOT / "evidence", ROOT / "harness"
AUTHOR = ("Alex Perrin", "44126061+AlexPerrin@users.noreply.github.com")
TRAILER = "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
GIT_ENV = {"GIT_AUTHOR_NAME": AUTHOR[0], "GIT_AUTHOR_EMAIL": AUTHOR[1], "GIT_COMMITTER_NAME": AUTHOR[0],
           "GIT_COMMITTER_EMAIL": AUTHOR[1], "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z"}
TRACK = {  # derived, not configured: the repo, the remotes fetched, the base, the dev ref of a change, the public act
    "client": {"repo": "client", "fetch": ["origin"], "base": "origin/HEAD", "dev": "origin/client/{slug}", "public": "release"},
    "server": {"repo": "fork", "fetch": ["origin", "fork"], "base": "origin/HEAD", "dev": "fork/dev/{slug}", "public": "upstream"},
    "harness": {"repo": "harness", "fetch": [], "base": "main", "dev": "harness/{slug}", "public": None},
}
PRIO = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
now = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
P = lambda s: Path(os.path.expanduser(str(s)))


def cfg():
    return yaml.safe_load((ROOT / "hd.yaml").read_text())


# ---------------------------------------------------------------- facts (P1: an unknown fact is None, never False)
class Facts:
    """Every read of the outside world, memoised per pass. Tests replace it with a dict-driven Fake."""

    def __init__(s):
        s.memo = {}

    def _m(s, key, f):
        if key not in s.memo:
            s.memo[key] = f()
        return s.memo[key]

    def sh(s, args, cwd=None, env=None, timeout=600):
        try:
            r = subprocess.run(args, cwd=cwd, env={**os.environ, **(env or {})}, capture_output=True, text=True, timeout=timeout)
            return r.returncode, r.stdout, r.stderr
        except (OSError, subprocess.TimeoutExpired):
            return None

    def fetch(s, clone, remote):
        return s._m(("fetch", clone, remote), lambda: (s.sh(["git", "-C", clone, "fetch", "-q", "--prune", remote]) or [1])[0] == 0)

    def rev(s, clone, ref):
        """sha | '' (no such ref) | None (unknown)."""
        r = s.sh(["git", "-C", clone, "rev-parse", "-q", "--verify", ref + "^{commit}"])
        return None if r is None else (r[1].strip() if r[0] == 0 else "")

    def contains(s, clone, tip, sha):
        if not tip or not sha:
            return None if tip is None else False
        r = s.sh(["git", "-C", clone, "merge-base", "--is-ancestor", sha, tip])
        return None if r is None or r[0] > 1 else r[0] == 0

    def tree(s, clone, commit):
        r = s.sh(["git", "-C", clone, "rev-parse", commit + "^{tree}"])
        return r[1].strip() if r and r[0] == 0 else None

    def merge(s, clone, base, head, msg):
        """R8: ('ok', commit) | ('conflict', detail) | None. The merged tree becomes a commit with fixed author and
        dates, so the same inputs give the same commit; a build copy checks it out, its tree sha keys every artefact."""
        def f():
            c = s.contains(clone, base, head)
            if c is None:
                return None
            if c:
                return "ok", base
            if s.contains(clone, head, base):
                return "ok", head
            r = s.sh(["git", "-C", clone, "merge-tree", "--write-tree", base, head])
            if r is None or r[0] > 1:
                return None
            if r[0] == 1:
                return "conflict", "\n".join(l for l in r[1].splitlines() if l.startswith("CONFLICT"))[:2000]
            r = s.sh(["git", "-C", clone, "commit-tree", r[1].split()[0], "-p", base, "-p", head, "-m", msg + "\n\n" + TRAILER], env=GIT_ENV)
            return ("ok", r[1].strip()) if r and r[0] == 0 else None
        return s._m(("merge", clone, base, head), f)

    def blob(s, clone, ref, path):
        r = s.sh(["git", "-C", clone, "rev-parse", "-q", "--verify", f"{ref}:{path}"])
        return None if r is None else (r[1].strip() if r[0] == 0 else "")

    def proc_start(s, pid):
        try:
            return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
        except OSError:
            return None

    def alive(s, pid, start):
        return bool(pid) and s.proc_start(pid) == str(start)

    def console(s):
        """The Claude session this command runs in: the nearest ancestor named claude, else the top ancestor."""
        pid = os.getppid()
        while pid > 1:
            try:
                stat = Path(f"/proc/{pid}/stat").read_text()
            except OSError:
                break
            if stat.split("(", 1)[1].rsplit(")", 1)[0] == "claude":
                break
            ppid = int(stat.rsplit(")", 1)[1].split()[1])
            if ppid <= 1:
                break
            pid = ppid
        return pid, s.proc_start(pid)

    def spawn(s, args, log, env=None):
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        p = subprocess.Popen(args, env={**os.environ, **(env or {})}, stdin=subprocess.DEVNULL, stdout=open(log, "a"),
                             stderr=subprocess.STDOUT, start_new_session=True)
        return p.pid, s.proc_start(p.pid)

    def run(s, cmd, cwd, env):
        """A contract script row, inline: (rc, output)."""
        r = s.sh(["bash", "-c", cmd], cwd=cwd, env=env, timeout=3600)
        return (1, "could not run") if r is None else (r[0], (r[1] + r[2])[-4000:])

    def events_count(s):
        f = STATE / "events.jsonl"
        return sum(1 for _ in open(f)) if f.exists() else 0


# ---------------------------------------------------------------- what is stored (P2) and nothing else
def _frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}, (m.group(2) if m else text)


def defs(kind):
    out = {}
    for f in sorted((DEFS / kind).glob("*.md")):
        meta, body = _frontmatter(f.read_text())
        meta.setdefault("slug", f.stem)
        meta.setdefault("deps", [])
        meta.setdefault("kind", "change")
        meta.setdefault("priority", "P2")
        meta["body"], meta["path"] = body, str(f)
        out[meta["slug"]] = meta
    return out


def track_root(c, track):
    """The dir holding the track's tools/track.sh and tools/track.md (the fork's on its tools branch worktree)."""
    r = c["repos"][TRACK[track]["repo"]]
    return P(r["path"]) / ".worktrees" / "harness" if r.get("tools") else P(r["path"])


def seed_rows(c, track):
    f = track_root(c, track) / "tools" / "track.md"
    part = f.read_text().split("## Seed rows", 1) if f.exists() else []
    return "\n".join(l for l in part[1].splitlines() if l.startswith("- ")) if len(part) == 2 else ""


def contract(slug):
    """evidence/<slug>/contract.md → {hash, rules, agreed, rows, text} | None.
    Rows `- id | text | check: <cmd>` (hand-over and gate) | `gate: <cmd>` (gate only) | `judge: <skill>` (qa)."""
    f = EVID / slug / "contract.md"
    if not f.exists():
        return None
    text = f.read_text()
    c = {"hash": hashlib.sha1(text.encode()).hexdigest()[:12], "rules": {}, "agreed": None, "rows": [], "text": text}
    for l in text.splitlines():
        if l.startswith("rules:"):
            c["rules"] = dict(kv.split("=", 1) for kv in l[6:].split() if "=" in kv)
        elif l.startswith("agreed:"):
            c["agreed"] = l[7:].strip() or None
        elif l.startswith("- ") and "|" in l:
            p = [x.strip() for x in l[2:].split("|")]
            row = {"id": p[0], "text": p[1] if len(p) > 1 else "", "check": None, "gate": None, "judge": None}
            for x in p[2:]:
                for k in ("check", "gate", "judge"):
                    if x.startswith(k + ":") or x == k:
                        row[k] = x[len(k) + 1:].strip() or k
            for k in ("check", "gate"):  # a row's command is a track script or a test run, never an arbitrary shell line
                if row[k] and not re.match(r"(\S*tools/\S+|python3 -m unittest\b|true$)", row[k]):
                    row[k] = f"false # refused: '{row[k]}' is not under tools/"
            c["rows"].append(row)
    return c


def write_contract(c, slug, track, agreed, rules=None):
    if not seed_rows(c, track):
        raise RuntimeError(f"no seed rows: {track_root(c, track) / 'tools' / 'track.md'} missing or without a '## Seed rows' section")
    f = EVID / slug / "contract.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"# Contract: {slug}\nrules: {' '.join(f'{k}={v}' for k, v in (rules or {}).items())}\nagreed: {agreed}\n\n{seed_rows(c, track)}\n")


def rec(slug, name):
    f = STATE / slug / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else None


def put(slug, name, obj):
    d = STATE / slug
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f".{name}.tmp"
    tmp.write_text(json.dumps({**obj, "ts": now()}, indent=1, sort_keys=True))
    os.replace(tmp, d / f"{name}.json")


def drop(slug, name):
    f = STATE / slug / f"{name}.json"
    if f.exists():
        f.unlink()


def verdicts(slug):
    f = STATE / slug / "verdicts.jsonl"
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []


def runs():
    d = STATE / "runs"
    return [json.loads(f.read_text()) for f in sorted(d.glob("*.json"))] if d.exists() else []


def save_run(r):
    (STATE / "runs").mkdir(parents=True, exist_ok=True)
    tmp = STATE / "runs" / f".{r['name']}.tmp"
    tmp.write_text(json.dumps(r, indent=1, sort_keys=True))
    os.replace(tmp, STATE / "runs" / f"{r['name']}.json")


def event(**e):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "events.jsonl", "a") as f:
        f.write(json.dumps({"ts": now(), **e}, sort_keys=True) + "\n")
    (STATE / "wake").write_text(now())


class lock:
    def __enter__(s):
        STATE.mkdir(parents=True, exist_ok=True)
        s.f = open(STATE / ".lock", "w")
        fcntl.flock(s.f, fcntl.LOCK_EX)

    def __exit__(s, *a):
        s.f.close()


# ---------------------------------------------------------------- the five nouns, derived
class Ctx:
    def __init__(s, facts=None, c=None):
        s.F, s.cfg = facts or Facts(), c or cfg()
        s.changes, s.goals = defs("changes"), defs("goals")
        s.runs, s.memo, s.alerts = runs(), {}, []

    def _m(s, k, f):
        if k not in s.memo:
            s.memo[k] = f()
        return s.memo[k]

    def clone(s, ch):
        return str(P(s.cfg["repos"][TRACK[ch["track"]]["repo"]]["path"]))

    def fetched(s, ch):
        return all(s.F.fetch(s.clone(ch), r) for r in TRACK[ch["track"]]["fetch"])

    def head(s, ch):
        """The change's commit: the tip of its dev ref (a release: the base tip). '' absent, None unknown."""
        t = TRACK[ch["track"]]
        return s._m(("head", ch["slug"]), lambda: s.F.rev(s.clone(ch), t["base"] if ch["kind"] == "release" else t["dev"].format(slug=ch["slug"])) if s.fetched(ch) else None)

    def base(s, ch):
        return s._m(("base", ch["track"]), lambda: s.F.rev(s.clone(ch), TRACK[ch["track"]]["base"]) if s.fetched(ch) else None)

    def live(s, ch, head):
        """A6: the target holds head. client: master; server: the test server's tree; harness: main."""
        if not head:
            return False
        if ch["track"] == "server":
            lv = rec("live", "tree") or {}
            return head in lv.get("heads", []) or bool(lv.get("commit") and s.F.contains(s.clone(ch), lv["commit"], head))
        return s.F.contains(s.clone(ch), s.base(ch), head)

    def done(s, ch, head):
        """A6: a server change when upstream main holds head; every other change when live."""
        if ch["track"] == "server" and ch["kind"] != "local":
            return s.F.contains(s.clone(ch), s.base(ch), head) if head else False
        return s.live(ch, head)

    def T(s, ch, head):
        """R8: base + each dependency's head not yet in base + head, merged in order."""
        def f():
            base, clone = s.base(ch), s.clone(ch)
            if not base:
                return None
            cur = base
            for d in ch["deps"]:
                dh = s.head(s.changes[d]) if d in s.changes else None
                if dh is None:
                    return None
                if dh and not s.F.contains(clone, base, dh):
                    r = s.F.merge(clone, cur, dh, f"T: {d} {dh[:9]}")
                    if r is None or r[0] != "ok":
                        return r and ("conflict", f"dependency {d}: {r[1]}")
                    cur = r[1]
            return s.F.merge(clone, cur, head, f"T: {ch['slug']} {head[:9]} onto {base[:9]}")
        return s._m(("T", ch["slug"], head), f)

    def tree(s, ch, commit):
        return s._m(("tree", commit), lambda: s.F.tree(s.clone(ch), commit))

    def script(s, ch):
        return str(track_root(s.cfg, ch["track"]) / "tools" / "track.sh")

    def env(s, ch, head, tc, tree):
        return {"SLUG": ch["slug"], "HEAD": head, "T": tree, "TCOMMIT": tc, "BASE": s.base(ch) or "", "EVIDENCE": str(EVID / ch["slug"]),
                "CLONE": s.clone(ch), "TRACK": ch["track"], "PUBLIC_BRANCH": ch.get("branch") or f"content/{ch['slug']}", "PR": str(ch.get("pr") or ""), "HD_ROOT": str(ROOT)}

    def alive_run(s, ch):
        return next((r for r in s.runs if r["change"] == ch["slug"] and not r.get("ended")), None)

    def proc(s, slug, name):
        p = rec(slug, f"proc-{name}")
        return None if not p else "alive" if s.F.alive(p["pid"], p["start"]) else "dead"

    def start(s, slug, name, args, env=None, act=True):
        """R5: start a track script once; one that died twice without its result is raised once."""
        st = s.proc(slug, name)
        if st == "alive":
            return
        p = rec(slug, f"proc-{name}") or {}
        if st == "dead" and p.get("attempts", 1) >= 2:
            s.alerts.append(f"{slug}: {name} died twice without a result (state/{slug}/{name}.log)")
            return
        if act:
            pid, start = s.F.spawn(args, STATE / slug / f"{name}.log", env)
            put(slug, f"proc-{name}", {"pid": pid, "start": start, "args": args, "attempts": p.get("attempts", 0) + 1})


def step(state, actor, **k):
    return {"state": state, "actor": actor, **k}


def texts(slug):
    d = EVID / slug
    return {n: (d / f).read_text().strip() if (d / f).exists() else "" for n, f in (("title", "pr-title.txt"), ("body", "pr-body.md"), ("comment", "pr-comment.md"))}


def digest(t):
    return hashlib.sha256(t.strip().encode()).hexdigest()[:16]


def nxt(ctx, ch):
    """The first unmet step of a change (docs/ARCHITECTURE.md, The loop); its state is a fact in words (R7)."""
    slug, track = ch["slug"], ch["track"]
    for d in ch["deps"]:
        dep = ctx.changes.get(d)
        if dep is None:
            return step(f"dependency {d} has no definition", "alert")
        dh = ctx.head(dep)
        if dh is None:
            return step(f"dependency {d}: ref unknown", "unknown")
        if not ctx.live(dep, dh):
            return step(f"waiting on {d}", "wait")
    con = contract(slug)
    if con is None:
        return step("contract: seed rows pending", "script", act=lambda: write_contract(ctx.cfg, slug, track, "derived" if track != "server" else ""))
    if not con["agreed"]:
        return step("contract: qa run due", "qa", mode="contract", input=con["hash"])
    head = ctx.head(ch)
    if head is None:
        return step("dev ref unknown", "unknown")
    ho = rec(slug, "handover")
    if head and ctx.done(ch, head) and (head != ctx.base(ch) or ch["kind"] == "release"):
        return step("done", "done")
    if not head or not ho or ho["head"] != head:
        hoff = EVID / slug / "handoff.md"
        return step("dev run due" if not head else f"dev run due: head {head[:9]} not handed over", "dev", mode="code",
                    input=[head, con["hash"], hoff.stat().st_mtime if hoff.exists() else 0])
    T = ctx.T(ch, head)
    if T is None:
        return step("tree unknown", "unknown")
    if T[0] == "conflict":
        return step("tree conflict: dev", "dev", mode="code", input=["conflict", head, con["hash"]], detail=T[1])
    tc = T[1]
    tree = ctx.tree(ch, tc)
    if tree is None:
        return step("tree unknown", "unknown")
    env, script = ctx.env(ch, head, tc, tree), ctx.script(ch)
    b = rec(slug, "build")
    if not b or b["T"] != tree:
        return step(f"building {tree[:9]}", "script", act=lambda: ctx.start(slug, "build", [script, "build", slug, tc], env))
    if not b["ok"]:
        return step("build failed: dev", "dev", mode="code", input=["build", tree, con["hash"]], detail=b.get("detail", ""))
    g = rec(slug, "gate")
    if not g or g["T"] != tree:
        return step(f"gate on {tree[:9]}", "script", act=lambda: ctx.start(slug, "gate", [script, "gate", slug, tc], env))
    if not g["ok"]:
        return step("gate failed: dev", "dev", mode="code", input=["gate", tree, con["hash"]], detail=g.get("detail", ""))
    if any(r["judge"] for r in con["rows"]):  # a reviewer judges only where the contract has judge rows (client: releases)
        vs = [v for v in verdicts(slug) if v["head"] == head and v["contract"] == con["hash"]]
        blobs = {k: ctx.F.blob(ctx.clone(ch), TRACK[track]["base"], k) for k in con["rules"]}
        if None in blobs.values():
            return step("upstream rule files unknown", "unknown")
        moved = [k for k, v in con["rules"].items() if blobs[k] != v]
        if moved and (not vs or any((vs[-1].get("rules") or {}).get(k) != blobs[k] for k in moved)):
            return step(f"upstream rules moved ({', '.join(moved)}): rule rows re-judged", "qa", mode="judge", input=[head, con["hash"], moved])
        if not vs:
            return step("review due", "qa", mode="judge", input=[head, con["hash"], []])
        failed = [k for k, r in vs[-1]["rows"].items() if r != "pass"]
        if failed:
            return step(f"FAIL {len(failed)} rows: dev", "dev", mode="code", input=["verdict", head, con["hash"], vs[-1]["ts"]],
                        detail="\n".join(f"{k}: {vs[-1]['rows'][k]}" for k in failed))
    if track == "server":
        if not ctx.live(ch, head):
            return step("gated; test server deploy pending", "ship-test")
        if ch["kind"] == "local":
            return step("live on the test server", "done")
        a = rec(slug, "approval")
        if not a or a["head"] != head:
            return step("live on the test server; waiting for the user's yes", "user", input=head)
        return step("shipping upstream", "script", act=lambda: ctx.start(slug, "ship", [str(ROOT / "hd-public"), "upstream", slug, head], env))
    if ch["kind"] == "release":
        a = rec(slug, "approval")
        if not a or a["head"] != head:
            return step(f"release v{ch['version']} at {head[:9]} waits for the user's yes", "user", input=head)
        return step(f"publishing v{ch['version']}", "script", act=lambda: ctx.start(slug, "ship", [str(ROOT / "hd-public"), "release", slug, head, f"v{ch['version']}"], env))
    return step("shipping", "script", act=lambda: ctx.start(slug, "ship", [script, "ship", slug, tc], env))


# ---------------------------------------------------------------- runs
def brief(ctx, ch, st, name, role):
    con, hoff = contract(ch["slug"]), EVID / ch["slug"] / "handoff.md"
    root = track_root(ctx.cfg, ch["track"])
    v = [x for x in verdicts(ch["slug"]) if x["head"] == ctx.head(ch)] if ch.get("path") else []
    lines = [f"# {role} run {name}: {ch['slug']} ({ch['track']}, {st.get('mode', role)})", "",
             f"Read {root}/tools/track.md, then run `python3 {ROOT}/hd.py show {ch['slug']}`.",
             f"Change: {ch.get('path', '')}  Evidence: {EVID / ch['slug']}  Contract: {EVID / ch['slug'] / 'contract.md'}",
             f"Clone: {ctx.clone(ch)}/.worktrees/{ch['slug']}  Build copy: {ctx.clone(ch)}/.worktrees/{ch['slug']}-build  Script: {root}/tools/track.sh",
             f"Dev ref: {TRACK[ch['track']]['dev'].format(slug=ch['slug'])}  Base: {TRACK[ch['track']]['base']}  Head now: {ctx.head(ch) or 'none'}",
             f"State: {st['state']}", ""]
    if st.get("detail"):
        lines += ["## Why", st["detail"], ""]
    if hoff.exists():
        lines += ["## Hand-off from your predecessor", hoff.read_text(), ""]
    if v and st.get("mode") == "code":
        lines += ["## Last verdict at this head", json.dumps(v[-1]["rows"], indent=1), ""]
    lines += ["## Definition", f"title: {ch.get('title', '')}  priority: {ch.get('priority', '')}  deps: {ch.get('deps', [])}  pr: {ch.get('pr', '')}", ch.get("body", ""), ""]
    if con:
        lines += ["## Contract", con["text"], ""]
    lines += ["## Hand back", "One line: `run <name>: handed over <sha>` | `run <name>: PASS` | `run <name>: FAIL n rows` | "
              "`run <name>: contract agreed` | `run <name>: ask <text>` | `run <name>: handoff`."]
    f = STATE / "briefs" / f"{name}.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("\n".join(lines))
    return str(f)


def dispatch(ctx, ch, st, act):
    """R2 R6: list a run for an unmet agent step once per input: no run of the change alive, no question open, no
    ended run on the same input without a hand-off, fewer than cfg.agents alive or listed."""
    role, slug = st["actor"], ch["slug"]
    if ctx.alive_run(ch) or rec(slug, "ask"):
        return
    inp = json.dumps(st.get("input"), sort_keys=True)
    same = [r for r in ctx.runs if r["change"] == slug and r["role"] == role and r.get("ended") and r.get("input") == inp]
    hoff = EVID / slug / "handoff.md"
    if same and not hoff.exists() and len(same) >= 2:  # R5: one retry, then raised once
        ctx.alerts.append(f"{slug}: {len(same)} {role} runs ended without a record on the same input; last: {(same[-1].get('last') or '')[:200]}")
        return
    if len([r for r in ctx.runs if not r.get("ended")]) >= ctx.cfg.get("agents", 3) or not act:
        return
    n = max([int(r["name"].rsplit("-", 1)[1]) for r in ctx.runs if r["change"] == slug and r["name"].rsplit("-", 1)[1].isdigit()] + [0]) + 1
    name, (cpid, cstart) = f"{slug}-{n}", ctx.F.console()
    r = {"name": name, "role": role, "change": slug, "step": st["state"], "input": inp, "mode": st.get("mode"), "brief": brief(ctx, ch, st, name, role),
         "console_pid": cpid, "console_start": cstart, "listed": now(), "events_at": ctx.F.events_count(), "started": None, "started_at": 0,
         "ended": None, "agent_id": None, "transcript": None, "record": False, "last": None, "usage": None}
    save_run(r)
    ctx.runs.append(r)
    event(change=slug, run=name, action="listed", role=role)


def orchestrate(ctx, view, act):
    """The orchestrator run: cross-track planning and monitoring. Listed when the facts call for it: an alert, a goal
    below target with nothing open, or 50 events since its last run ended (never on time)."""
    last = [r for r in ctx.runs if r["role"] == "orchestrator"]
    since = ctx.F.events_count() - (last[-1].get("events_at") or 0 if last else 0)
    why = view["alert"][:] + [g for g in view["goal"] if "planning due" in g] + ([f"{since} events since the last orchestrator run"] if since >= 50 else [])
    if why:
        pseudo = {"slug": "orchestrator", "track": "harness", "deps": [], "kind": "orchestrator", "priority": "P0", "body": "\n".join(why), "title": "orchestrate"}
        dispatch(ctx, pseudo, step("orchestrator run due: " + "; ".join(why)[:200], "orchestrator", mode="orchestrate", input=why), act)


def repairs(ctx, act):
    """R5: end the runs whose console is gone (their agents died with it)."""
    for r in ctx.runs:
        if not r.get("ended") and not ctx.F.alive(r.get("console_pid"), r.get("console_start")) and act:
            r["ended"], r["reason"] = now(), "console died"
            save_run(r)
            event(change=r["change"], run=r["name"], action="ended", reason="console died")


def tick(ctx=None, act=True):
    """One pass under the state lock → the view for `hd`. R1 (goals) and the integration deploy follow."""
    ctx = ctx or Ctx()
    view = {"spawn": [], "card": [], "question": [], "run": [], "goal": [], "change": [], "alert": []}
    with lock():
        repairs(ctx, act)
        for ch in sorted(ctx.changes.values(), key=lambda c: (PRIO.get(c["priority"], 9), c.get("created", ""), c["slug"])):
            st = nxt(ctx, ch)
            if st["actor"] == "script" and act:
                try:
                    st["act"]()
                except RuntimeError as e:
                    view["alert"].append(f"{ch['slug']}: {e}")
            elif st["actor"] in ("dev", "qa"):
                dispatch(ctx, ch, st, act)
            elif st["actor"] == "user":
                view["card"].append(card(ctx, ch, st))
            elif st["actor"] == "alert":
                view["alert"].append(f"{ch['slug']}: {st['state']}")
            if (a := rec(ch["slug"], "ask")):
                view["question"].append(f"{ch['slug']}: {a['text']}")
            last = rec(ch["slug"], "state")
            if st["actor"] != "done" or not last or last["state"] != "done":
                view["change"].append(f"{ch['slug']} [{ch['track']} {ch['priority']}]: {st['state']}")
            if act and (not last or last["state"] != st["state"]):
                put(ch["slug"], "state", {"state": st["state"]})
                event(change=ch["slug"], state=st["state"], detail=(st.get("detail") or "")[:300])
        view["alert"] += ctx.alerts
        orchestrate(ctx, view, act)
        for r in ctx.runs:
            if not r.get("ended"):
                (view["spawn"] if not r.get("started") else view["run"]).append(
                    f"{r['name']}: Agent(subagent_type=\"{r['role']}\", prompt=\"Read and follow {r['brief']}\")" if not r.get("started")
                    else f"{r['name']} ({r['role']}, {r['change']}) since {r['started']}")
    return view


def card(ctx, ch, st):
    head, t = st["input"], texts(ch["slug"])
    v = [x for x in verdicts(ch["slug"]) if x["head"] == head]
    lines = [f"## {ch['slug']}: {ch.get('title', '')}", f"head {head}  track {ch['track']}  evidence {EVID / ch['slug']}",
             f"verdict: {len(v[-1]['rows']) if v else 0} rows pass (run {v[-1].get('run', '?') if v else '?'})"]
    if ch["kind"] == "release":
        lines += [f"release v{ch['version']}: the APK in the evidence dir"]
    else:
        lines += [f"branch {ch.get('branch') or 'content/' + ch['slug']}" + (f", PR #{ch['pr']}" if ch.get("pr") else ", new draft PR"),
                  f"### title\n{t['title']}", f"### body\n{t['body']}", f"### comment\n{t['comment']}"]
    lines += [f"then: python3 {ROOT}/hd.py approve {ch['slug']} {head}"]
    return "\n".join(lines)


# ---------------------------------------------------------------- commands (a refusal lists every reason at once)
def refuse(*why):
    sys.exit("refused: " + "; ".join(why))


def cmd_show(a):
    slug = a[0]
    ch = defs("changes").get(slug) or defs("goals").get(slug) or refuse(f"no change or goal {slug}")
    print(Path(ch["path"]).read_text())
    con = contract(slug)
    print("\n## Contract\n" + (con["text"] if con else "none"))
    for n in ("handover", "build", "gate", "approval", "ask", "state"):
        if (r := rec(slug, n)):
            print(f"\n## {n}\n" + json.dumps(r, indent=1))
    for v in verdicts(slug):
        print(f"\n## verdict {v['ts']} head {v['head'][:9]} run {v.get('run', '')}\n" + json.dumps(v["rows"], indent=1))
    if (hoff := EVID / slug / "handoff.md").exists():
        print("\n## handoff.md\n" + hoff.read_text())
    for r in runs():
        if r["change"] == slug:
            print(f"\nrun {r['name']} {r['role']} listed {r['listed']} started {r.get('started')} ended {r.get('ended')} record {r.get('record')}: {(r.get('last') or '')[:200]}")


def cmd_handover(a):
    """R3: reads the pushed dev ref (no sha typed); every script row must pass; records {head, T}."""
    ctx = Ctx()
    ch = ctx.changes.get(a[0]) or refuse(f"no change {a[0]}")
    con = contract(ch["slug"])
    if not con or not con["agreed"]:
        refuse("no agreed contract")
    head = ctx.head(ch)
    if head is None:
        refuse("dev ref cannot be read")
    if not head:
        refuse(f"dev ref {TRACK[ch['track']]['dev'].format(slug=ch['slug'])} does not exist: push it")
    ev = EVID / ch["slug"]
    if len([f for f in ev.iterdir() if f.name != "contract.md"]) == 0:
        refuse(f"evidence dir {ev} holds nothing but the contract")
    T = ctx.T(ch, head)
    if T is None:
        refuse("tree cannot be computed")
    if T[0] == "conflict":
        refuse("conflict with the base or a dependency:\n" + T[1])
    tree = ctx.tree(ch, T[1])
    env = ctx.env(ch, head, T[1], tree)
    why = []
    for row in con["rows"]:
        if row["check"]:
            rc, out = ctx.F.run(row["check"], str(ROOT), env)
            if rc:
                why.append(f"row {row['id']} failed: {out.strip()[-400:]}")
    if why:
        refuse(*why)
    put(ch["slug"], "handover", {"head": head, "T": tree, "commit": T[1], "summary": " ".join(a[1:])})
    drop(ch["slug"], "ask")
    (EVID / ch["slug"] / "handoff.md").unlink(missing_ok=True)
    event(change=ch["slug"], record="handover", head=head)
    print(f"handed over {head} (tree {tree[:9]})")


def cmd_verdict(a):
    """R3: every contract row 'pass' or 'fail: <note>', appended, bound to head and the contract hash."""
    ctx = Ctx()
    ch = ctx.changes.get(a[0]) or refuse(f"no change {a[0]}")
    head = ctx.head(ch)
    if head != a[1]:
        refuse(f"head is {head or 'absent'}, not {a[1]}")
    con = contract(ch["slug"]) or refuse("no contract")
    rows = json.loads(Path(a[2]).read_text())
    why = ["rows missing: " + ", ".join(m)] if (m := [r["id"] for r in con["rows"] if r["id"] not in rows]) else []
    if (bad := [k for k, v in rows.items() if not (v == "pass" or str(v).startswith("fail"))]):
        why.append("rows must be 'pass' or 'fail: <note>': " + ", ".join(bad))
    if why:
        refuse(*why)
    (STATE / ch["slug"]).mkdir(parents=True, exist_ok=True)
    rules = {k: ctx.F.blob(ctx.clone(ch), TRACK[ch["track"]]["base"], k) for k in con["rules"]}
    with open(STATE / ch["slug"] / "verdicts.jsonl", "a") as f:
        f.write(json.dumps({"ts": now(), "head": head, "contract": con["hash"], "rows": rows, "rules": rules, "run": os.environ.get("HD_RUN", "")}, sort_keys=True) + "\n")
    failed = [k for k, v in rows.items() if v != "pass"]
    (EVID / ch["slug"] / "handoff.md").unlink(missing_ok=True)
    event(change=ch["slug"], record="verdict", head=head, failed=len(failed))
    print(f"verdict at {head[:9]}: {'PASS' if not failed else f'FAIL {len(failed)} rows'}")


def cmd_ask(a):
    slug, text = a[0], " ".join(a[1:])
    defs("changes").get(slug) or defs("goals").get(slug) or refuse(f"no change or goal {slug}")
    if rec(slug, "ask"):
        refuse("a question is already open on this change; it is answered first")
    if not text:
        refuse("empty question")
    put(slug, "ask", {"text": text})
    event(change=slug, record="ask", text=text[:300])
    print("asked")


def cmd_answer(a):
    """R3: the user's answer is a contract row, never free text; the open question is closed."""
    slug, text = a[0], " ".join(a[1:])
    ch = defs("changes").get(slug) or defs("goals").get(slug) or refuse(f"no change or goal {slug}")
    f = EVID / slug / "contract.md"
    if not f.exists():
        write_contract(cfg(), slug, ch["track"], "")
    n = sum(1 for l in f.read_text().splitlines() if l.startswith("- answer-")) + 1
    with open(f, "a") as o:
        o.write(f"- answer-{n} | {now()} the user: {text} | {'judge: qa-server' if ch['track'] == 'server' else 'note'}\n")
    drop(slug, "ask")
    event(change=slug, record="answer", text=text[:300])
    print(f"answer-{n} added to the contract")


def cmd_approve(a):
    """R4: only at the change's user step, bound to that head and the PR body's digest."""
    ctx = Ctx()
    ch = ctx.changes.get(a[0]) or refuse(f"no change {a[0]}")
    st = nxt(ctx, ch)
    if st["actor"] != "user" or st["input"] != a[1]:
        refuse(f"nothing to approve at {a[1]}: {st['state']}")
    put(ch["slug"], "approval", {"head": a[1], "body": digest(texts(ch["slug"])["body"])})
    event(change=ch["slug"], record="approval", head=a[1])
    print(f"approved {a[1]}")


def cmd_new(a):
    import argparse
    p = argparse.ArgumentParser(prog="hd new")
    p.add_argument("slug"); p.add_argument("--track", required=True, choices=list(TRACK)); p.add_argument("--title", required=True)
    p.add_argument("--kind", default="change", choices=["change", "release", "local"]); p.add_argument("--priority", default="P2")
    p.add_argument("--deps", default=""); p.add_argument("--goal"); p.add_argument("--branch"); p.add_argument("--pr", type=int)
    p.add_argument("--version"); p.add_argument("--network", action="store_true"); p.add_argument("--body", default="")
    o = p.parse_args(a)
    f = DEFS / "changes" / f"{o.slug}.md"
    if f.exists():
        refuse(f"{f} exists")
    meta = {k: v for k, v in vars(o).items() if v not in (None, "", False) and k != "body"}
    meta["deps"], meta["created"] = [d for d in o.deps.split(",") if d], now()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n" + o.body + "\n")
    event(change=o.slug, action="new", track=o.track)
    print(str(f))


def cmd_tick(a):
    v = tick(act="--dry-run" not in a)
    for k, lines in v.items():
        for l in lines:
            print(f"{k}: {l}" if k != "card" else l)


def main(argv):
    cmds = {"show": cmd_show, "handover": cmd_handover, "verdict": cmd_verdict, "ask": cmd_ask, "answer": cmd_answer,
            "approve": cmd_approve, "new": cmd_new, "tick": cmd_tick}
    if not argv:
        return cmd_tick([])
    if argv[0] not in cmds:
        sys.exit(f"hd: commands: {' '.join(cmds)}")
    cmds[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
