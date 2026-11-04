"""Step → the world (docs/ARCHITECTURE.md §4, §6): config and definitions, candidates, briefs, jobs in systemd scopes,
the wake file, and the pass itself (tick)."""
import fcntl
import functools
import glob
import json
import os
import subprocess
import sys

import yaml

import decide
import observe
import publish
import store
from decide import Cfg, Change, Goal, Step, Track
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

@functools.lru_cache(maxsize=1)
def cfg() -> Cfg:
    """hd.yaml and every track's recipe, read once per process (a pass, a command)."""
    y = yaml.safe_load(open(os.path.join(ROOT, "hd.yaml")))
    tracks = {}
    for name, r in y["repos"].items():
        script = os.path.join(ROOT, "tracks", name, "track.sh")
        recipes = {}
        if os.access(script, os.X_OK):
            out = subprocess.run([script, "recipe"], capture_output=True, text=True).stdout
            recipes = dict(line.split(None, 1) for line in out.splitlines() if " " in line)
        path = os.path.normpath(os.path.join(ROOT, os.path.expanduser(r["path"])))
        tracks[name] = Track(name, r["name"], path, r["base"], r.get("upstream", ""), r.get("prefix", "dev"), recipes, r.get("remote", ""), tuple(r.get("pins") or ()))
    return Cfg(agents=y["agents"], hold=y.get("hold") or "", tracks=tracks, builds=y.get("builds", 3))


def tier(p) -> str:
    """A priority as written ('P1', 'p1', 1, '1') → the tier; anything else P2 (a definition never halts the pass)."""
    p = str(p).strip().upper()
    p = p if p.startswith("P") else "P" + p
    return p if p in decide.TIERS else "P2"


def parse_change(path) -> Change:
    text = open(path).read()
    _, fm, body = text.split("---\n", 2)
    y = yaml.safe_load(fm) or {}
    title = next((l[2:] for l in body.splitlines() if l.startswith("# ")), "")
    return Change(slug=y.get("slug") or os.path.basename(path)[:-3], track=y["track"], kind=y.get("kind", "change"),
                  upstream=y.get("upstream", True), priority=tier(y.get("priority", "P2")), deps=tuple(y.get("deps") or ()),
                  goal=y.get("goal", ""), units=tuple(y.get("units") or ()), pr=y.get("pr", 0) or 0,
                  public=y.get("public", ""), branch=y.get("branch", ""), title=title, body=body)


DEFS = os.path.join(ROOT, "harness")   # the definitions: changes/ and goals/; `hd tick --defs` reads another tree's (the replay, the fixtures)


def changes() -> list:
    return [parse_change(p) for p in sorted(glob.glob(os.path.join(DEFS, "changes", "*.md")))]


def goals() -> list:
    out = []
    for p in sorted(glob.glob(os.path.join(DEFS, "goals", "*.md"))):
        _, fm, body = open(p).read().split("---\n", 2)
        y = yaml.safe_load(fm)
        out.append(Goal(y["slug"], y["track"], float(y["target"]), y.get("measure", "script"), body))
    return out


def measure_query(db, g, T, tree) -> None:
    """The server-content goal: inventory units (harness/goals/<goal>.json) named in `units:` of a change landed on the
    goal's tree with a passing verdict, over all units → a measure row."""
    units = {u["unit"] for u in json.load(open(os.path.join(DEFS, "goals", f"{g.slug}.json")))}
    L = store.Ledger(db)
    passed = set()
    for ch in changes():
        if ch.goal == g.slug and L.landed(ch.slug, decide.STAGING if T.upstream else T.base):
            v = L.one("SELECT ok FROM verdict WHERE change=? ORDER BY id DESC LIMIT 1", ch.slug)
            if v and v["ok"]:
                passed |= set(ch.units) & units
    value = 100.0 * len(passed) / len(units) if units else 0.0
    db.execute("INSERT OR REPLACE INTO measure(goal, tree, value, report, at) VALUES (?,?,?,?,?)",
               (g.slug, tree, value, json.dumps(sorted(passed)), now()))
    event(db, "measure", g.slug, None, f"{value:g}% at {tree[:12]}")


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


def stage(db, ch, T, head: str) -> None:
    """Merge a checked head into the track's staging (worktree <repo>/.worktrees/staging, created from base plus the track's pins
    once); push it to the fork. A conflict → merge --abort and event('merge-conflict', '<head7> <files>'), the dev's step
    (dev_due); a pin that no longer merges → alert('pin-conflict')."""
    wt = os.path.join(T.path, ".worktrees", "staging")
    if not os.path.isdir(wt):
        if subprocess.run(["git", "-C", T.path, "show-ref", "--verify", "-q", decide.STAGING]).returncode == 0:
            git(T.path, "worktree", "add", wt, "staging")
        else:
            git(T.path, "worktree", "add", "-b", "staging", wt, T.base)
            for pin in T.pins:
                r = subprocess.run(["git", "-C", wt, "merge", "--no-ff", "--no-edit", f"{T.remote}/{pin}"], capture_output=True, text=True)
                if r.returncode:   # all or nothing: the next pass starts again once the pin merges (the user's rebase of it)
                    git(wt, "merge", "--abort", check=False)
                    git(T.path, "worktree", "remove", "--force", wt, check=False)
                    git(T.path, "branch", "-D", "staging", check=False)
                    store.alert(db, "pin-conflict", pin, r.stdout[-300:])
                    return
    r = subprocess.run(["git", "-C", wt, "merge", "--no-ff", "--no-edit", head], capture_output=True, text=True)
    if r.returncode:
        files = " ".join(l.split()[-1] for l in r.stdout.splitlines() if l.startswith("CONFLICT"))
        git(wt, "merge", "--abort", check=False)
        event(db, "merge-conflict", ch.slug, None, f"{head[:7]} {files}")
        return
    git(wt, "push", "-q", T.remote, "staging")
    event(db, "merged", ch.slug, None, f"{head[:7]} into staging {git(wt, 'rev-parse', '--short', 'HEAD')}")


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
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) < 3:
            continue   # not a seed line
        rid, text, how, *flags = parts
        kind, _, cmd = how.partition(":")
        if kind == "judge" and not cmd.strip():
            cmd = None
        if "upstream" in flags and not (T.upstream and ch.upstream):
            continue
        db.execute("INSERT OR IGNORE INTO criterion(change, rid, kind, text, cmd, source, upstream_only, created_at) VALUES (?,?,?,?,?,'seed',?,?)",
                   (ch.slug, rid, kind, text, cmd.strip() if cmd else None, int("upstream" in flags), now()))


def clone(T, ch, create=True) -> str:
    """The change's worktree <repo>/.worktrees/<slug> on its dev branch, created from base when missing (a listed run
    or a job needs it; `hd show` only names it)."""
    path = os.path.join(T.path, ".worktrees", ch.slug)
    if create and not os.path.isdir(path):
        branch = f"{T.prefix}/{ch.slug}"
        if subprocess.run(["git", "-C", T.path, "show-ref", "--verify", "-q", T.dev_ref(ch)]).returncode == 0:
            git(T.path, "worktree", "add", "-B", branch, path, T.dev_ref(ch))
        elif subprocess.run(["git", "-C", T.path, "show-ref", "--verify", "-q", f"refs/heads/{branch}"]).returncode == 0:
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
           (f"goal {ch.slug}: file the changes that close its gap with hd new --track {T.name} --goal {ch.slug}; write no code"
            if step.mode == "plan" else f"clone {clone(T, ch, create=False)}") + f"   evidence {evidence}   logs {STATE}/{ch.slug}/",
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
        out.append(f"{c['rid']:<12} {c['kind']:<8} {res}" + (f"   {'cmd' if c['kind'] == 'script' else 'skill'}: {c['cmd']}" if c["cmd"] else ""))
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
    if step.mode != "plan":
        clone(T, ch)   # the run's worktree exists before its brief names it
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


def job_env(db, ch, T, s, **more) -> dict:
    """The environment of a job and of every scripted criterion: HD_* and the short names the scripts read."""
    base = git(T.path, "rev-parse", T.base)
    cl = T.path if ch.slug == "staging" or ch.kind == "goal" else clone(T, ch)   # a job of staging or a goal has no dev clone
    env = dict(os.environ, HD_ROOT=ROOT, HD_DB=db_path(db), HD_SLUG=ch.slug, HD_TREE=s["tree"], HD_TCOMMIT=s["tcommit"],
               HD_HEAD=s["head"], HD_BASE=T.base, HD_REPO=T.path, HD_CLONE=cl, HD_BUILDS=str(cfg().builds),
               SLUG=ch.slug, HEAD=s["head"], T=decide.built(s), TCOMMIT=s["tcommit"], BASE=base, CLONE=cl,
               BUILD=os.path.join(T.path, ".worktrees", f"{ch.slug}-build"), EVIDENCE=os.path.join(ROOT, "evidence", ch.slug),
               PR=str(ch.pr or ""), PUBLIC_BRANCH=ch.public or "")
    comp = json.loads(s["composite_json"] or "{}") if "composite_json" in s.keys() else {}
    for lib in ("central", "filestore"):
        if lib in comp:
            env[lib.upper()] = f"{cfg().tracks[lib].path}:{comp[lib]['head']}"
    env.update(more)
    return env


def start(db, step: Step, ch, T) -> None:
    """systemd-run --user --scope --unit hd-<slug>-<kind>-<key12> -- tracks/<t>/track.sh <verb> <slug> <key>;
    the job row holds pid, pid_start, scope and log. The script's last act is `hd job <kind> <key> ok|fail <detail>`
    (a gate: `hd gate`); the wrapper writes its exit to state/<slug>/<kind>-<key12>.rc."""
    L = store.Ledger(db)
    if ch.slug == "staging" or step.kind == "measure":
        ref = decide.STAGING if T.upstream else T.base
        sha = L.ref(T.name, ref)
        s = {"tree": L.ref_tree(T.name, ref), "tcommit": sha, "head": sha}
    elif step.kind == "publish":
        s = L.submission(ch.slug, L.latest_card(ch.slug)["head"])
    else:
        s = L.submission(ch.slug, L.ref(T.name, T.dev_ref(ch)))
    k12 = step.key.replace(":", "-")[:12] if step.kind != "ship" else step.key.split(":")[-1][:12]
    unit = f"hd-{ch.slug}-{step.kind}-{k12}"
    unit = unit.replace("/", "-")
    d = os.path.join(STATE, ch.slug)
    os.makedirs(d, exist_ok=True)
    log, rc = os.path.join(d, f"{step.kind}-{k12}.log"), os.path.join(d, f"{step.kind}-{k12}.rc")
    env = job_env(db, ch, T, s, HD_KIND=step.kind, HD_KEY=step.key, HD_LOG=log, HD_RC=rc)
    script = os.path.join(ROOT, "tracks", T.name, "track.sh")
    cmd = ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", unit, "--", "bash", "-c",
           '"$@"; r=$?; echo $r > "$HD_RC"; exit $r', "bash", script, step.kind, ch.slug, step.key]
    if step.kind == "publish":
        cmd[-4:] = [sys.executable, os.path.join(ROOT, "harness", "hd.py"), "publish", step.key]
    if os.path.exists(rc):
        os.remove(rc)
    subprocess.run(["systemctl", "--user", "stop", unit + ".scope"], capture_output=True)   # a prior attempt's leftovers hold the name
    p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=open(log, "ab"), stderr=subprocess.STDOUT,
                         env=env, cwd=ROOT, start_new_session=True)
    db.execute("""INSERT INTO job(kind, key, change, pid, pid_start, scope, log, started_at) VALUES (?,?,?,?,?,?,?,?)
                  ON CONFLICT(kind, key) DO UPDATE SET pid=excluded.pid, pid_start=excluded.pid_start, scope=excluded.scope,
                  log=excluded.log, started_at=excluded.started_at, ended_at=NULL, exit=NULL""",
               (step.kind, step.key, ch.slug, p.pid, observe.pid_start(p.pid), unit, log, now()))


# --- the wake and the pass -------------------------------------------------------------------------------------

WAKE_KINDS = ("run", "ended", "drain")   # what the orchestrator acts on; the driver watches the ledger itself


def wake(db) -> None:
    """Rewrite state/wake.orchestrator when events the orchestrator acts on (a listed run, an ended run, a drain) are newer than the file's header."""
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


def tick(path=None, dry_run=False, offline=False, defs=None) -> list:
    """One pass: observe (unless offline) → decide.plan → act (unless dry_run). Returns the actions.
    A second tick while one runs exits at once (flock on state/tick.lock). defs: another tree's definitions (dry runs)."""
    global DEFS
    DEFS = defs or DEFS
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
    gs = goals()
    if not offline and not dry_run:   # a dry run writes nothing: it plans over the ledger as observed
        for T in {ch.track for ch in open_} | {g.track for g in gs if g.track in c.tracks}:   # a goal's repo moves without a change
            T = c.tracks[T]
            moved = observe.fetch(db, T)
            targets = {T.done_ref(ch) for ch in open_ if ch.track == T.name} | ({decide.STAGING} if T.upstream else set())
            for target in targets & moved:
                observe.landed(db, T, target, [x for x in open_ if x.track == T.name])
        for ch in open_:
            T = c.tracks[ch.track]
            if T.upstream and ch.upstream:
                observe.texts(db, ch.slug)
                if ch.pr:
                    observe.pr(db, T, ch, ours=(publish.OWNER,))
        observe.procs(db)
        observe.sessions(db, definition_blob())
        observe.runs(db)
        observe.stacks(db)
        observe.alerts(db)
    for ch in open_:
        if not L.landed(ch.slug, c.tracks[ch.track].done_ref(ch)):
            seed(db, ch, c.tracks[ch.track])
    try:
        actions = decide.plan(L, defs, c, gs)
    except Exception as e:   # the pass never dies silently: the fault is an alert the driver sees, the next pass tries again
        if dry_run:
            raise
        store.alert(db, "fault", "pass", f"plan raised {type(e).__name__}: {e}"[:300])
        wake(db)
        return []
    if dry_run:
        return actions
    draining = (L.live_session() or {"drain_at": None})["drain_at"]
    for a in actions:
        s = a.step
        if a.change.endswith(":staging"):
            T = c.tracks[a.change.split(":")[0]]
            ch = Change("staging", T.name, upstream=False)
        elif a.change.startswith("goal:"):
            g = next(x for x in gs if x.slug == a.change[5:])
            T = c.tracks[g.track]
            ch = Change(g.slug, g.track, kind="goal", upstream=False, body=g.body)
            if s.kind == "measure" and g.measure == "query":
                measure_query(db, g, T, s.key.split(":")[0])
                continue
        else:
            ch = next(x for x in defs if x.slug == a.change)
            T = c.tracks[ch.track]
        try:
            if s.kind == "run" and not draining:
                brief(db, ch, T, s)
            elif s.kind in ("build", "gate", "ship", "deploy", "measure", "publish"):
                start(db, s, ch, T)
            elif s.kind == "merge":
                stage(db, ch, T, s.key.split(":")[1])
            elif s.kind == "card":
                publish.card(db, ch, T, s.key, L.pr(T.upstream, ch.pr) if ch.pr else None, L.texts(ch.slug), s.input)
        except Exception as e:   # one change's act failing never stops the others'
            store.alert(db, "fault", f"act:{ch.slug}", f"{s.kind} raised {type(e).__name__}: {e}"[:300])
            continue
        last = L.last_event(ch.slug, "state")
        if not last or last["detail"] != f"{s.kind}: {s.why}":
            event(db, "state", ch.slug, None, f"{s.kind}: {s.why}")
    wake(db)
    return actions


def stop_scope(run_id) -> None:
    """End a run's processes: its scope, and the Windows programs its scripts recorded under state/winpids/<scope>/."""
    unit = f"hd-run-{run_id}.scope"
    d = os.path.join(STATE, "winpids", unit)
    for pid in os.listdir(d) if os.path.isdir(d) else []:
        subprocess.run(["/mnt/c/Windows/System32/taskkill.exe", "/F", "/T", "/PID", pid], capture_output=True)
        os.remove(os.path.join(d, pid))
    subprocess.run(["systemctl", "--user", "stop", unit], capture_output=True)


def tick_later() -> None:
    """Start a pass without waiting for it (after a command, a run end): the flock serialises."""
    subprocess.Popen([sys.executable, os.path.join(ROOT, "harness", "hd.py"), "tick"], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
