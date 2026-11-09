"""ledger → Step: next(change) and the pass's plan (docs/ARCHITECTURE.md §3).

Pure: takes a Ledger, the parsed definitions and the config; no subprocess, no network, no clock. Tested over
recorded ledger snapshots (tests/fixtures/), never over fakes of git or GitHub.
"""
import json
from dataclasses import dataclass, field

from store import Ledger, digest

TIERS = ["P0", "P1", "P2", "P3", "P4"]
ATTEMPTS = 3            # starts of one job key without a result before the pass stops restarting it (alert 'attempts')


@dataclass(frozen=True)
class Change:
    """A parsed harness/changes/<slug>.md: front matter + body."""
    slug: str
    track: str              # client | fork | central | filestore | devtools | harness
    kind: str = "change"    # change | release
    upstream: bool = True   # False: fork only, never a PR
    priority: str = "P2"    # P0..P4
    deps: tuple = ()
    goal: str = ""
    units: tuple = ()
    pr: int = 0
    public: str = ""        # the PR branch on the fork (content/<x>, fix/<x>), moved only by a publish
    draft: bool = False     # the user's word: its card leaves the PR a draft (no ready step)
    branch: str = ""        # the dev ref; default refs/heads/<track prefix>/<slug>
    title: str = ""
    body: str = ""


@dataclass(frozen=True)
class Goal:
    """A parsed harness/goals/<slug>.md: measured by a script (`track.sh measure`) or by a ledger query."""
    slug: str
    track: str
    target: float
    measure: str = "script"   # script | query
    body: str = ""


@dataclass(frozen=True)
class Track:
    """One hd.yaml repo: where a track's changes live and what its script can do."""
    name: str               # the hd.yaml key == Change.track
    repo: str               # GitHub name
    path: str               # local clone
    base: str               # full ref the candidate starts from: refs/heads/main, refs/remotes/upstream/main
    upstream: str = ""      # upstream GitHub name; "" for the tracks that ship by fast-forward
    prefix: str = "dev"     # dev branch prefix
    recipes: dict = field(default_factory=dict)   # verb → version string from `track.sh recipe`
    remote: str = ""        # the remote dev refs are pushed to; "" when the dev ref stays local (the harness)
    pins: tuple = ()        # (branch, slug) of the fork's local branches, merged into staging after the base, in order; slug "" or the change that supersedes it

    def dev_ref(self, ch):
        if ch.branch:
            return ch.branch
        return f"refs/remotes/{self.remote}/{self.prefix}/{ch.slug}" if self.remote else f"refs/heads/{self.prefix}/{ch.slug}"

    def candidate_base(self):
        """The ref a candidate starts from: staging on a track that deploys the test server (proved on what the server
        runs, H4), else base; the PR head itself stays on base (G4)."""
        return STAGING if self.upstream and "deploy" in self.recipes else self.base

    def done_ref(self, ch):
        """Where a landed row means done: the live branch, upstream main, or staging for a fork-only change."""
        return self.base if (not self.upstream or ch.upstream) else "refs/heads/staging"


@dataclass(frozen=True)
class Cfg:
    agents: int = 7
    builds: int = 3
    hold: str = ""          # the held band, e.g. "P2": tiers below it do not run
    free: int = 0           # GB: below it on a build disk, no build starts (observe.disk alerts)
    tracks: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Step:
    kind: str               # done|wait|run|build|gate|merge|card|publish|ship|measure|release
    why: str                # printed by `hd`; the event detail
    role: str = ""          # dev|qa for kind == run
    mode: str = ""          # code|criteria|judge|plan
    input: str = ""         # digest of the brief's inputs; a run is due while no run exists with this input
    key: str = ""           # the job's key


@dataclass(frozen=True)
class Action:
    change: str
    step: Step


@dataclass(frozen=True)
class Ctx:
    L: Ledger
    cfg: Cfg
    defs: dict              # slug → Change, every definition parsed


DONE = Step("done", "done")


def tip(C, ch):
    return C.L.ref(C.cfg.tracks[ch.track].name, C.cfg.tracks[ch.track].dev_ref(ch))


def sub(C, ch):
    t = tip(C, ch)
    return C.L.submission(ch.slug, t) if t else None


def built(s) -> str:
    """The tree built, T: <tree>[_c<central tree12>][_f<filestore tree12>], a composite keyed by every tree built in;
    a valid docker tag (or:<T>), so the key, the jobs' T and the image name agree."""
    comp = json.loads(s["composite_json"] or "{}") if "composite_json" in s.keys() else {}
    return s["tree"] + "".join(f"_{k[0]}{v['tree'][:12]}" for k, v in sorted(comp.items()))


def key(C, ch, kind, s):
    """<T>:<recipe> (built)."""
    return f"{built(s)}:{C.cfg.tracks[ch.track].recipes.get(kind, '')}"


def short(key) -> str:
    """A key's short form: the tree's first 12, or a ship's commit."""
    return key.split(":")[-1][:12] if key.startswith("refs/") else key[:12]


def job_due(C, kind, k):
    """A job Step for (kind, key) unless it holds a result or is running; None when ok=1."""
    j = C.L.job(kind, k)
    if j and j["ok"] == 1:
        return None
    if j and j["ok"] == 0:
        return Step("wait", f"{kind} failed: {j['detail']}")
    if j and j["pid"] and not j["ended_at"]:
        return Step("wait", f"{kind} running ({short(k)})")
    if C.L.attempts(kind, k, C.L.harness_shipped_at(C.cfg.tracks["harness"])) >= ATTEMPTS:
        return Step("wait", f"{kind} {short(k)}: {ATTEMPTS} starts without a result since the harness last shipped")
    return Step(kind, f"{kind} {short(k)}", key=k)


# --- guards: each returns a Step or None; first non-None wins ---------------------------------------------------

def done(C, ch) -> bool:
    """A change is done when closed, landed where its track says done, or, fork-only on a track that does not stage
    (nothing to land on), when its head's verdict is ok."""
    T = C.cfg.tracks[ch.track]
    if C.L.closed(ch.slug) or C.L.landed(ch.slug, T.done_ref(ch)):
        return True
    if T.upstream and not ch.upstream and not stages(C, ch):
        t = tip(C, ch)
        v = C.L.last_verdict(ch.slug, t) if t else None
        return bool(v and v["ok"])
    return False


def closed(C, ch):
    """Closed, folded, or landed where it is done → done, whatever is added later."""
    if done(C, ch):
        return DONE
    return None


LIBRARY = ("central", "filestore")   # the libraries the server builds in as a Gradle composite
SERVER = ("fork",) + LIBRARY


def server_deps(C, ch) -> list:
    """ch's deps on the server tracks, with theirs, transitively."""
    out, todo = [], list(ch.deps)
    while todo:
        d = C.defs.get(todo.pop())
        if d and d.track in SERVER and d.slug not in out:
            out.append(d.slug)
            todo += d.deps
    return out


def candidate_deps(get, ch) -> list:
    """ch's deps for its candidate, each after its own: a same-track dep's deps build with it, transitively (a fix two
    deps down is in the candidate too)."""
    out = []
    def walk(c):
        for dep in c.deps:
            if dep not in out:
                d = get(dep)
                if d.track == ch.track:
                    walk(d)
                if dep not in out:
                    out.append(dep)
    walk(ch)
    return out


def deps_live(C, ch):
    """A dep with nothing to build on → wait. A submitted dep of the same track joins the candidate (its landing is
    waited for before the card or the ship, upstream_dep_wait); a dep on another track (a harness fix the dev filed, a
    library the server needs) is nothing to build on until it lands or closes. A server fix that runs on the test server
    is there once live: a change on another track builds on it then, its PR held or not (an upstream merge gates only the
    dep's own track, upstream_dep_wait). Off the server tracks a library dep too is there only once live (a client, the
    live stack and its desktops reach the test server alone)."""
    for dep in ch.deps:
        d = C.defs.get(dep)
        if d is None:
            return Step("wait", f"dep {dep} has no definition")
        if d.track != ch.track and (stages(C, d) and d.track not in LIBRARY or ch.track not in SERVER and d.track in SERVER):
            for x in [dep] + server_deps(C, d):   # a server dep works there only with its own deps
                if not (C.L.closed(x) or C.L.landed(x, "live")):
                    return Step("wait", f"dep {x} not live on the test server")
            continue
        if done(C, d):
            continue
        if d.track != ch.track and d.track not in LIBRARY:
            return Step("wait", f"dep {dep} ({d.track}) not landed")
        if not C.L.one("SELECT 1 FROM submission WHERE change=?", dep):
            return Step("wait", f"dep {dep}")
        s = sub(C, d)   # a head that failed its gate cannot ship: nothing to build on until its dev resubmits
        j = C.L.job("gate", key(C, d, "gate", s)) if s and "gate" in C.cfg.tracks[d.track].recipes else None
        if j and j["ok"] == 0:
            return Step("wait", f"dep {dep} gate failed at {s['head'][:7]}")
    return None


def ask_open(C, ch):
    a = C.L.open_ask(ch.slug)
    return Step("wait", f"question {a['id']}: {a['text']}") if a else None


def criteria_due(C, ch):
    T = C.cfg.tracks[ch.track]
    if not (T.upstream and ch.upstream):
        return None
    if C.L.runs_with_record(ch.slug, "criteria", "criteria agreed"):
        return None
    return Step("run", "criteria before code", role="qa", mode="criteria", input=digest("criteria", ch.slug))


def outdated(C, ch, v) -> bool:
    """A FAIL verdict older than a dep's landing: what it failed on may be the dep, so the head is judged again before a dev re-runs."""
    if not v or v["ok"]:
        return False
    at = [C.L.one("SELECT max(at) a FROM landed WHERE change=?", d)["a"] for d in ch.deps]
    return any(x and x > v["at"] for x in at)


def dev_due(C, ch):
    t, s = tip(C, ch), sub(C, ch)
    why = []
    if not t:
        why.append("new")
    elif not s:
        why.append(f"no submission at {t[:7]}")
    else:
        if C.L.criteria_after(ch.slug, s["at"]):
            why.append("criteria added since the submission")
        v = C.L.last_verdict(ch.slug, t)
        if v and not v["ok"] and not outdated(C, ch, v):
            why.append(f"verdict FAIL at {t[:7]} (run {v['run']})")
        for kind in ("build", "gate"):
            j = C.L.job(kind, key(C, ch, kind, s))
            if j and j["ok"] == 0:
                why.append(f"{kind} failed: {j['detail']}")
        j = C.L.job("ship", f"{C.cfg.tracks[ch.track].base}:{s['tcommit']}")
        if j and j["ok"] == 0:
            why.append(f"ship failed: {j['detail']}")
        e = C.L.last_event(ch.slug, "merge-conflict") if stages(C, ch) else None
        if e and e["detail"].split()[:2] == [t[:7], (C.L.ref(C.cfg.tracks[ch.track].name, STAGING) or "")[:7]]:   # a moved staging is merged again first
            why.append(f"merge conflict on staging: {e['detail']}")
        e = C.L.last_event(ch.slug, "ci-failed")
        if e and e["detail"].startswith(t[:7]):
            why.append(f"CI failed at {t[:7]}: {e['detail'][8:]}")
    if not why:
        return None
    answers = [a["ask"] for a in C.L.answers_since(ch.slug, s["at"] if s else "")]
    landed = [d for d in ch.deps if d in C.defs and done(C, C.defs[d])]
    if ch.track not in SERVER:
        landed += [d for d in server_deps(C, ch) if C.L.landed(d, "live")]   # a server dep live on the test server is its dependent's new fact
    return Step("run", "; ".join(why), role="dev", mode="code", input=digest(t, why, answers, landed))   # a dep landing is a new fact: the dev runs again


def build_due(C, ch):
    T = C.cfg.tracks[ch.track]
    return job_due(C, "build", key(C, ch, "build", sub(C, ch))) if "build" in T.recipes else None


def gate_due(C, ch):
    T = C.cfg.tracks[ch.track]
    if "gate" not in T.recipes:
        return Step("wait", f"tracks/{T.name}/track.sh has no gate")
    return job_due(C, "gate", key(C, ch, "gate", sub(C, ch)))


def judge_due(C, ch):
    judged = C.L.criteria(ch.slug, "judge")
    if not judged:
        return None
    t = tip(C, ch)
    d = digest([(c["rid"], c["text"]) for c in judged])
    v = C.L.last_verdict(ch.slug, t)
    if v and v["criteria_digest"] == d and not outdated(C, ch, v):
        return None
    return Step("run", f"judge: {len(judged)} criteria at {t[:7]}", role="qa", mode="judge",
                input=digest(t, d, v["id"]) if outdated(C, ch, v) else digest(t, d))   # a re-judge is a new input: the failed one does not park it


STAGING = "refs/heads/staging"


def stages(C, ch):
    """Staging exists to deploy the test server: a track with an upstream and a deploy recipe merges into it, and so
    does a library the server builds in (its own staging is the deploy's composite, store.staging_composite)."""
    T = C.cfg.tracks[ch.track]
    return bool(T.upstream and ("deploy" in T.recipes or ch.track in LIBRARY))


def stage_due(C, ch):
    """Tracks with a deploy recipe: a checked head not yet on staging → merge (act.stage); a conflict of this head with the staging tip it names is dev_due's."""
    if not stages(C, ch) or C.L.landed(ch.slug, STAGING):
        return None
    for dep in ch.deps:   # staging runs the head alone, not its candidate: a dep merges first, so the test server never runs a change without it
        d = C.defs.get(dep)
        if d and stages(C, d) and not done(C, d) and not C.L.landed(dep, STAGING):
            return Step("wait", f"dep {dep} not yet on staging")
    t = tip(C, ch)
    return Step("merge", f"merge {t[:7]} into staging", key=f"staging:{t}")


def upstream_dep_wait(C, ch):
    """A public act or a ship waits until every same-track dep is landed where it is done (G4: a PR holds no other PR's
    commits); a library dep holds a public act too. A dep on another track holds neither: deps_live already waited for
    it to land or go live, and its PR may wait in the outbound queue meanwhile."""
    for dep in ch.deps:
        d = C.defs.get(dep)
        if d and not done(C, d) and (d.track == ch.track or is_public(C, ch) and d.track in LIBRARY):
            return Step("wait", f"dep {dep} not yet landed on {C.cfg.tracks[d.track].done_ref(d).split('/')[-1]}")
    return None


def is_public(C, ch):
    T = C.cfg.tracks[ch.track]
    return bool(T.upstream and ch.upstream)


def texts_due(C, ch):
    """An upstream change needs its texts before a card: title and body for a new PR, the comment for every head, a
    reply file per finding → run dev (text work only)."""
    if not is_public(C, ch):
        return None
    t, texts = tip(C, ch), C.L.texts(ch.slug)
    missing = [n for n in (("pr-comment.md",) if ch.pr else ("pr-title.txt", "pr-body.md", "pr-comment.md")) if not texts.get(n, "").strip()]
    missing += [f"pr-reply-{f['comment_id']}.md" for f in C.L.findings(ch.slug) if f"pr-reply-{f['comment_id']}.md" not in texts]
    if not missing:
        return None
    return Step("run", "texts: " + ", ".join(missing), role="dev", mode="code", input=digest(t, missing))


def card_due(C, ch):
    """No card at this head, or its approval spent by a refusal, or texts observed since it was shown → card
    (publish.card computes the acts and texts; the same digest is the same card)."""
    if not is_public(C, ch):
        return None
    t = tip(C, ch)
    c = C.L.latest_card(ch.slug)
    if c and c["head"] == t:
        a = C.L.one("SELECT spent_why FROM approval WHERE card=?", c["id"])
        texts_moved = C.L.one("SELECT 1 FROM text WHERE change=? AND at>?", ch.slug, c["shown_at"])
        refused = a and a["spent_why"] and a["spent_why"] != "published"
        if not refused and not texts_moved:
            return None
        if refused:
            return Step("card", f"card at {t[:7]} after a refusal", key=t, input=a["spent_why"])
    return Step("card", f"card at {t[:7]}", key=t)


def approval_wait(C, ch):
    if not is_public(C, ch):
        return None
    c = C.L.latest_card(ch.slug)
    if not c or C.L.one("SELECT 1 FROM approval WHERE card=?", c["id"]):
        return None
    if C.L.hold(ch.slug, c["head"]):
        return Step("wait", f"held: card {c['id']} hidden")
    return Step("wait", f"the user: card {c['id']} at {c['head'][:7]}")


def publish_due(C, ch):
    if not is_public(C, ch):
        return None
    c = C.L.latest_card(ch.slug)
    if not c or not C.L.approval(c["id"]) or not C.L.undone_steps(c["id"]):
        return None
    e = C.L.last_event(ch.slug, "ci-failed")
    if e and e["detail"].startswith(c["head"][:7]):
        return None   # dev_due lists the dev; the approval stays
    return job_due(C, "publish", str(c["id"]))


def published_wait(C, ch):
    T = C.cfg.tracks[ch.track]
    if not (T.upstream and ch.upstream):
        return None
    return None if C.L.landed(ch.slug, T.done_ref(ch)) else Step("wait", "maintainers")


def ship_due(C, ch):
    T = C.cfg.tracks[ch.track]
    if T.upstream or C.L.landed(ch.slug, T.base):
        return None
    k = f"{T.base}:{sub(C, ch)['tcommit']}"
    j = C.L.job("ship", k)
    if j and j["ok"] == 1:
        return Step("wait", f"shipped {k.split(':')[1][:7]}, not yet landed on {T.base}")
    return job_due(C, "ship", k)


def goal_tree(C, g):
    """The tree a goal is measured on: the live branch, or staging for a server track."""
    T = C.cfg.tracks[g.track]
    return C.L.ref_tree(T.name, STAGING if T.upstream else T.base)


def measure_due(C, g):
    tree = goal_tree(C, g)
    if not tree or C.L.measure(g.slug, tree):
        return None
    return job_due(C, "measure", f"{tree}:{C.cfg.tracks[g.track].recipes.get('measure', g.measure)}")   # running, failed or parked → wait


def plan_due(C, g):
    """Below target and no open change naming the goal → one dev run in plan mode, which files changes and no code."""
    m = C.L.measure(g.slug)
    if not m or m["value"] >= g.target:
        return None
    for ch in C.defs.values():
        if ch.goal == g.slug and not done(C, ch):
            return None
    return Step("run", f"{g.slug} at {m['value']:g}% of {g.target:g}, nothing open", role="dev", mode="plan", input=digest(g.slug, m["tree"]))


GOAL_GUARDS = [measure_due, plan_due]


def owner_live(C, owner) -> bool:
    """An artifact owner is live while its fact holds: a job running, a run not ended, a change open (<slug>), or a
    tree the change still names (<slug>@<T>: its current head's, its latest card's, a running job's or a live run's;
    staging@<T>: the staging tree)."""
    kind, _, rest = owner.partition(":")
    if kind == "job":
        k, _, key = rest.partition(":")
        j = C.L.job(k, key)
        return bool(j and j["pid"] and not j["ended_at"])
    if kind == "run":
        return bool(C.L.one("SELECT 1 FROM run WHERE id=? AND ended_at IS NULL", rest))
    slug, at, t = owner.partition("@")
    if slug in ("staging", "live"):
        t = t.partition("_")[0]   # a deploy's T carries the composite suffix; its job key and the staging ref name the plain tree
    if at and C.L.one("SELECT 1 FROM job WHERE key LIKE ? AND pid IS NOT NULL AND ended_at IS NULL", t + ":%"):
        return True
    if slug in ("staging", "live"):
        return not at or bool(C.L.one("SELECT 1 FROM ref WHERE name=? AND tree=?", STAGING, t))
    if C.L.live_run(slug):
        return True
    ch = C.defs.get(slug)
    if ch is None or ch.track not in C.cfg.tracks or done(C, ch):
        return False
    if not at:
        return True
    s, c = sub(C, ch), C.L.latest_card(slug)
    cs = C.L.submission(slug, c["head"]) if c else None
    return any(x and built(x) == t for x in (s, cs))


def release_due(C) -> list:
    """Every recorded artifact no live owner names → a release step (act.release: the verb, then its absence observed)."""
    return [Action("release", Step("release", f"release {kind} {key}: {', '.join(owners)} no longer live", key=f"{kind}:{key}"))
            for kind, key, owners in C.L.artifacts() if not any(owner_live(C, o) for o in owners)]


GUARDS = [
    closed, deps_live, ask_open, criteria_due, dev_due, build_due, gate_due, judge_due, stage_due,
    upstream_dep_wait, texts_due, card_due, approval_wait, publish_due, published_wait, ship_due,
]


def next(C, ch) -> Step:
    for guard in GUARDS:
        step = guard(C, ch)
        if step:
            return step
    return DONE


def priority(ch, blocked: dict) -> str:
    """min tier over {ch} ∪ the open changes ch blocks (transitively); a harness change is P1 at least."""
    tiers, seen, todo = [ch.priority], set(), [ch.slug]
    while todo:
        s = todo.pop()
        for b in blocked.get(s, ()):
            if b.slug not in seen:
                seen.add(b.slug)
                tiers.append(b.priority)
                todo.append(b.slug)
    best = min(tiers, key=TIERS.index)
    return min(best, "P1", key=TIERS.index) if ch.track == "harness" else best


def parked(L: Ledger, slug, input):
    """The run with this input that parks the step: one that ended by its own hand-back, or a listing withdrawn by a stop
    before it started (a new fact makes a new input). One that died with its console, handed off or was stopped once
    started did not do the work: it gets a successor, None; repeats are the run-lost alert."""
    p = L.run_for(slug, input)
    return p if p and p["end_kind"] not in ("console", "handoff") and not (p["end_kind"] == "stop" and p["started_at"]) else None


def plan(L: Ledger, changes: list, cfg: Cfg, goals: list = ()) -> list:
    """The pass's action list: next() per open change in priority order (harness, then PR rounds, then new content;
    below cfg.hold skipped); a run Step listed only while live runs < cfg.agents and no run with this input parks it
    (parked); a job Step only while no job of its key (a ship: of its branch) is in flight."""
    C = Ctx(L, cfg, {c.slug: c for c in changes})
    open_ = [c for c in changes if not L.closed(c.slug) and c.track in cfg.tracks]
    blocked = {}
    for c in open_:
        for d in c.deps:
            blocked.setdefault(d, []).append(c)
    tier = {c.slug: priority(c, blocked) for c in open_}
    open_.sort(key=lambda c: (0 if c.track == "harness" else 1 if c.pr else 2, TIERS.index(tier[c.slug]), c.slug))
    live = len(L.live_runs())
    low = L.disk_below(cfg.free) if cfg.free else []   # below the level no new build starts (a gate builds)
    actions = []
    for g in goals:
        if g.track not in cfg.tracks:
            continue
        s = None
        for guard in GOAL_GUARDS:
            s = guard(C, g)
            if s:
                break
        if s and s.kind == "run" and (live >= cfg.agents or parked(L, g.slug, s.input) or L.live_run(g.slug)):
            continue
        if s:
            actions.append(Action(f"goal:{g.slug}", s))
            live += s.kind == "run"
    for T in cfg.tracks.values():   # the test server runs staging: one deploy per staging tree
        tree = L.ref_tree(T.name, STAGING) if T.upstream and "deploy" in T.recipes else None
        if tree:
            try:   # the libraries' staging moves the deploy too
                tree = built({"tree": tree, "composite_json": L.staging_composite(STAGING)})
            except ValueError:
                pass   # two library heads: act.start raises it as the deploy's fault
            s = job_due(C, "deploy", f"{tree}:{T.recipes['deploy']}")
            if s and s.kind == "deploy" and L.jobs_in_flight("deploy"):
                s = Step("wait", "a deploy is running")
            if s and s.kind == "deploy" and L.live_users():   # a deploy recreates the stack under whoever plays on it
                s = Step("wait", f"{', '.join(L.live_users())} on the live stack")
            if s and s.kind == "deploy" and low:
                s = None   # a deploy builds: none below the disk level
            if s and s.kind != "wait":
                actions.append(Action(f"{T.name}:staging", s))
    for c in open_:
        if cfg.hold and TIERS.index(tier[c.slug]) > TIERS.index(cfg.hold):
            continue
        s = next(C, c)
        r = L.live_run(c.slug)
        if r and s is not DONE:
            actions.append(Action(c.slug, Step("wait", f"run {r['id']} {r['role']} {'live' if r['started_at'] else 'listed'}")))
            continue
        if s.kind == "run":
            prior = parked(L, c.slug, s.input)
            if prior:
                s = Step("wait", f"run {prior['id']} ended ({prior['end_kind']}) with this input: {s.why}")
            elif live >= cfg.agents:
                s = Step("wait", f"{cfg.agents} runs live: {s.why}")
            else:
                live += 1
        elif s.kind in ("build", "gate") and low:
            s = Step("wait", f"disk: {low[0]['path']} {low[0]['free'] // 10**9} GB free, below {cfg.free} GB: {s.why}")
        elif s.kind in ("build", "gate", "ship", "publish") and L.jobs_in_flight(s.kind, s.key.split(":")[0] + ":" if s.kind == "ship" else s.key):
            s = Step("wait", f"a {s.kind} of this {'branch' if s.kind == 'ship' else 'key'} is running")
        actions.append(Action(c.slug, s))
    return actions + release_due(C)
