"""Step → the world (docs/ARCHITECTURE.md §4, §6): config and definitions, candidates, briefs, jobs in systemd scopes,
the wake file, and the pass itself (tick)."""
import fcntl
import glob
import os
import subprocess
import sys

import yaml

import decide
import observe
import store
from decide import Cfg, Change, Step, Track
from store import ROOT, STATE, event, now

AUTHOR = "Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>"
TRAILER = "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
HD = f"python3 {ROOT}/harness/hd.py"


class Conflict(Exception):
    """merge-tree conflict; args[0] is the list of files."""


def is_ancestor(path, a, b) -> bool:
    return subprocess.run(["git", "-C", path, "merge-base", "--is-ancestor", a, b]).returncode == 0


def git(path, *args, check=True, env=None):
    r = subprocess.run(["git", "-C", path, *args], capture_output=True, text=True, env=env)
    if check and r.returncode:
        raise subprocess.CalledProcessError(r.returncode, r.args, r.stdout, r.stderr)
    return r.stdout.strip()


# --- config and definitions ------------------------------------------------------------------------------------

def cfg() -> Cfg:
    y = yaml.safe_load(open(os.path.join(ROOT, "hd.yaml")))
    tracks = {}
    for name, r in y["repos"].items():
        script = os.path.join(ROOT, "tracks", name, "track.sh")
        recipes = {}
        if os.access(script, os.X_OK):
            out = subprocess.run([script, "recipe"], capture_output=True, text=True).stdout
            recipes = dict(line.split(None, 1) for line in out.splitlines() if " " in line)
        path = os.path.normpath(os.path.join(ROOT, os.path.expanduser(r["path"])))
        tracks[name] = Track(name, r["name"], path, r["base"], r.get("upstream", ""), r.get("prefix", "dev"), recipes)
    return Cfg(agents=y["agents"], hold=y.get("hold") or "", tracks=tracks)


def parse_change(path) -> Change:
    text = open(path).read()
    _, fm, body = text.split("---\n", 2)
    y = yaml.safe_load(fm) or {}
    title = next((l[2:] for l in body.splitlines() if l.startswith("# ")), "")
    return Change(slug=y.get("slug") or os.path.basename(path)[:-3], track=y["track"], kind=y.get("kind", "change"),
                  upstream=y.get("upstream", True), priority=y.get("priority", "P2"), deps=tuple(y.get("deps") or ()),
                  goal=y.get("goal", ""), units=tuple(y.get("units") or ()), pr=y.get("pr", 0) or 0,
                  branch=y.get("branch", ""), title=title, body=body)


def changes() -> list:
    return [parse_change(p) for p in sorted(glob.glob(os.path.join(ROOT, "harness", "changes", "*.md")))]


# --- candidates and keys ---------------------------------------------------------------------------------------

def candidate(path, base: str, heads: list) -> tuple:
    """(tree, tcommit): the head itself when it descends from base; else merge-tree folded over base and each head,
    committed with the newest parent's date so the same inputs give the same commit. Raises Conflict(files)."""
    if len(heads) == 1 and is_ancestor(path, base, heads[0]):
        return git(path, "rev-parse", heads[0] + "^{tree}"), heads[0]
    cur = base
    for h in heads:
        r = subprocess.run(["git", "-C", path, "merge-tree", "--write-tree", "--name-only", cur, h], capture_output=True, text=True)
        lines = r.stdout.splitlines()
        if r.returncode:
            raise Conflict(lines[1:lines.index("")] if "" in lines else lines[1:])
        date = max(git(path, "log", "-1", "--format=%cI", p) for p in (cur, h))
        env = dict(os.environ, GIT_AUTHOR_NAME="Alex Perrin", GIT_AUTHOR_EMAIL=AUTHOR.split("<")[1][:-1],
                   GIT_COMMITTER_NAME="Alex Perrin", GIT_COMMITTER_EMAIL=AUTHOR.split("<")[1][:-1],
                   GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        cur = git(path, "commit-tree", lines[0], "-p", cur, "-p", h, "-m", f"candidate: merge {h[:7]}", env=env)
    return git(path, "rev-parse", cur + "^{tree}"), cur


def seed(db, ch, T):
    """INSERT OR IGNORE the track's seed criteria (tracks/<t>/track.md '## Seed criteria': `- rid | text | script: cmd`)."""
    path = os.path.join(ROOT, "tracks", T.name, "track.md")
    if not os.path.exists(path):
        return
    section = open(path).read().split("## Seed criteria", 1)
    if len(section) < 2:
        return
    for line in section[1].splitlines():
        if not line.startswith("- "):
            continue
        rid, text, how = (p.strip() for p in line[2:].split("|", 2))
        kind, cmd = ("script", how.split(":", 1)[1].strip()) if how.startswith("script:") else ("judge", None)
        db.execute("INSERT OR IGNORE INTO criterion(change, rid, kind, text, cmd, source, created_at) VALUES (?,?,?,?,?,'seed',?)",
                   (ch.slug, rid, kind, text, cmd, now()))


def clone(T, ch) -> str:
    """The change's worktree <repo>/.worktrees/<slug> on its dev branch, created from base when missing."""
    path = os.path.join(T.path, ".worktrees", ch.slug)
    if not os.path.isdir(path):
        branch = T.dev_ref(ch).removeprefix("refs/heads/")
        if subprocess.run(["git", "-C", T.path, "show-ref", "--verify", "-q", T.dev_ref(ch)]).returncode == 0:
            git(T.path, "worktree", "add", path, branch)
        else:
            git(T.path, "worktree", "add", "-b", branch, path, T.base)
    return path


# --- briefs ----------------------------------------------------------------------------------------------------

def brief_text(db, ch, T, step: Step, run_id) -> str:
    L = store.Ledger(db)
    t = L.ref(T.name, T.dev_ref(ch))
    s = L.submission(ch.slug, t) if t else None
    evidence = os.path.join(ROOT, "evidence", ch.slug)
    head = f"run {run_id}" if run_id else "no run"
    out = [f"# {head}: {step.role or 'show'} {ch.slug} ({T.name}, {ch.priority})   step: {step.why}",
           f"clone {clone(T, ch)}   evidence {evidence}   logs {STATE}/{ch.slug}/",
           f"rules tracks/{T.name}/track.md   hd = {HD}", "",
           "## definition", ch.body.strip(), ""]
    crit = L.criteria(ch.slug)
    out.append(f"## criteria @candidate {s['tree'][:12] if s else 'none'}   (rid  kind  result)")
    checks = L.check_results(s["tree"]) if s else {}
    v = L.last_verdict(ch.slug, t) if t else None
    marks = {r["criterion_id"]: r for r in db.execute("SELECT * FROM verdict_row WHERE verdict=?", (v["id"],))} if v else {}
    for c in crit:
        if c["kind"] == "script":
            r = checks.get(c["id"])
            res = "not run" if r is None else ("ok" if r["ok"] else f"FAIL: {r['note']}")
        else:
            m = marks.get(c["id"])
            res = "not judged" if m is None else (m["result"] + (f": {m['note']}" if m["note"] else "") + f" @{t[:7]}")
        out.append(f"{c['rid']:<12} {c['kind']:<8} {res}" + (f"   cmd: {c['cmd']}" if c["cmd"] else ""))
    since = s["at"] if s else ""
    out += ["", "## since your last submission" if s else "## answers and findings"]
    for a in db.execute("SELECT n.*, a.text, a.options_json FROM answer n JOIN ask a ON a.id=n.ask WHERE a.change=? AND n.at>?", (ch.slug, since)):
        out.append(f"answer {a['ask']} ({a['by']}): option {a['option']} {a['words'] or ''}   to: {a['text']}")
    for f in db.execute("SELECT * FROM finding WHERE change=? AND triage='finding' AND seen_at>?", (ch.slug, since)):
        out.append(f"finding {f['comment_id']} by {f['author']}: {f['body']}")
    for kind in ("build", "gate", "ship"):
        for j in db.execute("SELECT * FROM job WHERE change=? AND kind=? AND ok IS NOT NULL ORDER BY ended_at DESC LIMIT 1", (ch.slug, kind)):
            out.append(f"{kind} {j['key'][:12]}: {'ok' if j['ok'] else 'FAIL'} {j['detail'] or ''}   log {j['log']}")
    handoff = os.path.join(evidence, "handoff.md")
    if os.path.exists(handoff):
        out += ["", "## hand-off from your predecessor", open(handoff).read().strip()]
    record = {"code": f"submitted <sha>", "criteria": "criteria agreed", "judge": "PASS | run {id}: FAIL <n> criteria",
              "plan": "filed <slug>"}.get(step.mode, "")
    out += ["", f"## hand back exactly:  run {run_id or '<id>'}: {record}", ""]
    return "\n".join(out)


def brief(db, ch, T, step: Step) -> int:
    """INSERT the run and write state/briefs/<id>.md; returns the run id."""
    rid = db.execute("INSERT INTO run(change, role, mode, input, brief, listed_at) VALUES (?,?,?,?,?,?)",
                     (ch.slug, step.role, step.mode, step.input, "", now())).lastrowid
    path = os.path.join(STATE, "briefs", f"{rid}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(brief_text(db, ch, T, step, rid))
    db.execute("UPDATE run SET brief=? WHERE id=?", (os.path.relpath(path, ROOT), rid))
    event(db, "run", ch.slug, rid, f"{step.role} {step.mode}: {step.why}")
    return rid


# --- jobs ------------------------------------------------------------------------------------------------------

def db_path(db) -> str:
    return db.execute("PRAGMA database_list").fetchone()[2]


def start(db, step: Step, ch, T) -> None:
    """systemd-run --user --scope --unit hd-<slug>-<kind>-<key12> -- tracks/<t>/track.sh <verb> <slug> <key>;
    the job row holds pid, pid_start, scope and log. The script's last act is `hd job <kind> <key> ok|fail <detail>`
    (a gate: `hd gate`); the wrapper writes its exit to state/<slug>/<kind>-<key12>.rc."""
    L = store.Ledger(db)
    s = L.submission(ch.slug, L.ref(T.name, T.dev_ref(ch)))
    k12 = step.key.replace(":", "-")[:12] if step.kind != "ship" else step.key.split(":")[-1][:12]
    unit = f"hd-{ch.slug}-{step.kind}-{k12}"
    d = os.path.join(STATE, ch.slug)
    os.makedirs(d, exist_ok=True)
    log, rc = os.path.join(d, f"{step.kind}-{k12}.log"), os.path.join(d, f"{step.kind}-{k12}.rc")
    env = dict(os.environ, HD_ROOT=ROOT, HD_DB=db_path(db), HD_SLUG=ch.slug, HD_KIND=step.kind, HD_KEY=step.key,
               HD_TREE=s["tree"], HD_TCOMMIT=s["tcommit"], HD_HEAD=s["head"], HD_BASE=T.base, HD_REPO=T.path,
               HD_CLONE=clone(T, ch), HD_LOG=log, HD_RC=rc)
    script = os.path.join(ROOT, "tracks", T.name, "track.sh")
    cmd = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit, "--", "bash", "-c",
           '"$@"; r=$?; echo $r > "$HD_RC"; exit $r', "bash", script, step.kind, ch.slug, step.key]
    if os.path.exists(rc):
        os.remove(rc)
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=open(log, "ab"), stderr=subprocess.STDOUT,
                         env=env, cwd=ROOT, start_new_session=True)
    db.execute("""INSERT INTO job(kind, key, change, pid, pid_start, scope, log, started_at) VALUES (?,?,?,?,?,?,?,?)
                  ON CONFLICT(kind, key) DO UPDATE SET pid=excluded.pid, pid_start=excluded.pid_start, scope=excluded.scope,
                  log=excluded.log, started_at=excluded.started_at, ended_at=NULL, exit=NULL""",
               (step.kind, step.key, ch.slug, p.pid, observe.pid_start(p.pid), unit, log, now()))


# --- the wake and the pass -------------------------------------------------------------------------------------

WAKE_KINDS = ("run", "card", "question", "triage", "alert", "drain")


def wake(db) -> None:
    """Rewrite state/wake.orchestrator when events the orchestrator acts on are newer than the file's header."""
    path = os.path.join(STATE, "wake.orchestrator")
    seen = 0
    if os.path.exists(path):
        first = open(path).readline()
        seen = int(first.split()[-1]) if first.startswith("# through ") else 0
    rows = db.execute(f"SELECT * FROM event WHERE id>? AND kind IN ({','.join('?' * len(WAKE_KINDS))}) ORDER BY id",
                      (seen, *WAKE_KINDS)).fetchall()
    if rows:
        lines = [f"# through {rows[-1]['id']}"] + [f"{r['kind']:<9}{r['change'] or ''}  {r['detail']}" for r in rows]
        open(path, "w").write("\n".join(lines) + "\n")


def definition_blob() -> str:
    return store.digest(*(open(os.path.join(ROOT, f)).read() for f in (".claude/agents/orchestrator.md", ".mcp.json")))


def tick(path=None, dry_run=False, offline=False) -> list:
    """One pass: observe (unless offline) → decide.plan → act (unless dry_run). Returns the actions.
    A second tick while one runs exits at once (flock on state/tick.lock)."""
    os.makedirs(STATE, exist_ok=True)
    lock = open(os.path.join(STATE, "tick.lock"), "w")
    if not dry_run:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return []
    db = store.connect(path)
    c, defs = cfg(), changes()
    L = store.Ledger(db)
    open_ = [ch for ch in defs if not L.closed(ch.slug) and ch.track in c.tracks]
    if not offline:
        for T in {c.tracks[ch.track] for ch in open_}:
            moved = observe.fetch(db, T)
            for ch in open_:
                if ch.track == T.name and T.done_ref(ch) in moved:
                    observe.landed(db, T, T.done_ref(ch), [x for x in open_ if x.track == T.name])
        observe.procs(db)
        observe.sessions(db, definition_blob())
        observe.alerts(db)
    for ch in open_:
        seed(db, ch, c.tracks[ch.track])
    actions = decide.plan(L, defs, c)
    if dry_run:
        return actions
    draining = (L.live_session() or {"drain_at": None})["drain_at"]
    for a in actions:
        ch, s = next(x for x in defs if x.slug == a.change), a.step
        T = c.tracks[ch.track]
        if s.kind == "run" and not draining:
            brief(db, ch, T, s)
        elif s.kind in ("build", "gate", "ship"):
            start(db, s, ch, T)
        last = L.last_event(ch.slug, "state")
        if not last or last["detail"] != f"{s.kind}: {s.why}":
            event(db, "state", ch.slug, None, f"{s.kind}: {s.why}")
    wake(db)
    return actions


def tick_later() -> None:
    """Start a pass without waiting for it (after a command, a run end): the flock serialises."""
    subprocess.Popen([sys.executable, os.path.join(ROOT, "harness", "hd.py"), "tick"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
