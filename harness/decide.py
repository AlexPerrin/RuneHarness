"""ledger → Step: next(change) and the pass's plan (docs/ARCHITECTURE.md §3).

Pure: takes a Ledger, the parsed definitions and the config; no subprocess, no network, no clock. Tested over
recorded ledger snapshots (tests/fixtures/), never over fakes of git or GitHub.
"""
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
    branch: str = ""        # the dev ref; default refs/heads/<track prefix>/<slug>
    title: str = ""
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

    def dev_ref(self, ch):
        if ch.branch:
            return ch.branch
        return f"refs/remotes/{self.remote}/{self.prefix}/{ch.slug}" if self.remote else f"refs/heads/{self.prefix}/{ch.slug}"

    def done_ref(self, ch):
        """Where a landed row means done: the live branch, upstream main, or staging for a fork-only change."""
        return self.base if (not self.upstream or ch.upstream) else "refs/heads/staging"


@dataclass(frozen=True)
class Cfg:
    agents: int = 7
    builds: int = 3
    hold: str = ""          # the held band, e.g. "P2": tiers below it do not run
    tracks: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Step:
    kind: str               # done|wait|run|build|gate|merge|card|publish|ship|measure
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


def key(C, ch, kind, s):
    return f"{s['tree']}:{C.cfg.tracks[ch.track].recipes.get(kind, '')}"


def short(key) -> str:
    """A key's short form: the tree's first 12, or a ship's commit."""
    return key.split(":")[-1][:12] if key.startswith("refs/") else key[:12]


def job_due(C, kind, k):
    """A job Step for (kind, key) unless it holds a result or is running; None when ok=1."""
    j = C.L.job(kind, k)
    if j and j["ok"] == 1:
        return None
    if j and j["pid"] and not j["ended_at"]:
        return Step("wait", f"{kind} running ({short(k)})")
    if C.L.attempts(kind, k) >= ATTEMPTS:
        return Step("wait", f"{kind} {short(k)}: {ATTEMPTS} starts without a result")
    return Step(kind, f"{kind} {short(k)}", key=k)


# --- guards: each returns a Step or None; first non-None wins ---------------------------------------------------

def closed(C, ch):
    return DONE if C.L.closed(ch.slug) else None


def deps_live(C, ch):
    for dep in ch.deps:
        d = C.defs.get(dep)
        if d is None:
            return Step("wait", f"dep {dep} has no definition")
        if C.L.closed(dep):
            continue
        if not C.L.landed(dep, C.cfg.tracks[d.track].done_ref(d)):
            return Step("wait", f"dep {dep}")
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
        if v and not v["ok"]:
            why.append(f"verdict FAIL at {t[:7]} (run {v['run']})")
        for kind in ("build", "gate"):
            j = C.L.job(kind, key(C, ch, kind, s))
            if j and j["ok"] == 0:
                why.append(f"{kind} failed: {j['detail']}")
        j = C.L.job("ship", f"{C.cfg.tracks[ch.track].base}:{s['tcommit']}")
        if j and j["ok"] == 0:
            why.append(f"ship failed: {j['detail']}")
        e = C.L.last_event(ch.slug, "merge-conflict")
        if e and e["detail"].startswith(t[:7]):
            why.append(f"merge conflict on staging: {e['detail']}")
    if not why:
        return None
    last = C.L.last_run(ch.slug)
    successor = last["id"] if last and last["end_kind"] in ("console", "handoff") else None
    answers = [a["ask"] for a in C.L.answers_since(ch.slug, s["at"] if s else "")]
    return Step("run", "; ".join(why), role="dev", mode="code", input=digest(t, why, answers, successor))


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
    if v and v["criteria_digest"] == d:
        return None
    return Step("run", f"judge: {len(judged)} criteria at {t[:7]}", role="qa", mode="judge", input=digest(t, d))


STAGING = "refs/heads/staging"


def stage_due(C, ch):
    """Server tracks: a checked head not yet on staging → merge (act.stage); a recorded conflict of this head is dev_due's."""
    T = C.cfg.tracks[ch.track]
    if not T.upstream or C.L.landed(ch.slug, STAGING):
        return None
    t = tip(C, ch)
    return Step("merge", f"merge {t[:7]} into staging", key=f"staging:{t}")


def upstream_dep_wait(C, ch):
    return None  # shortcut: phase 2 (a dep in another PR not landed upstream)


def texts_due(C, ch):
    return None  # shortcut: phase 2 (pr-comment.md and reply files against the live PR)


def card_due(C, ch):
    return None  # shortcut: phase 2 (publish.card)


def approval_wait(C, ch):
    return None  # shortcut: phase 2


def publish_due(C, ch):
    return None  # shortcut: phase 2


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


def measure_due(C, ch):
    return None  # shortcut: phase 4 (goals)


def plan_due(C, ch):
    return None  # shortcut: phase 4 (goals)


GUARDS = [
    closed, deps_live, ask_open, criteria_due, dev_due, build_due, gate_due, judge_due, stage_due,
    upstream_dep_wait, texts_due, card_due, approval_wait, publish_due, published_wait, ship_due, measure_due, plan_due,
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


def plan(L: Ledger, changes: list, cfg: Cfg) -> list:
    """The pass's action list: next() per open change in priority order (harness, then PR rounds, then new content;
    below cfg.hold skipped); a run Step listed only while live runs < cfg.agents and no run exists for (change,
    input); a job Step only while no job of its key (a ship: of its branch) is in flight."""
    C = Ctx(L, cfg, {c.slug: c for c in changes})
    open_ = [c for c in changes if not L.closed(c.slug) and c.track in cfg.tracks]
    blocked = {}
    for c in open_:
        for d in c.deps:
            blocked.setdefault(d, []).append(c)
    tier = {c.slug: priority(c, blocked) for c in open_}
    open_.sort(key=lambda c: (0 if c.track == "harness" else 1 if c.pr else 2, TIERS.index(tier[c.slug]), c.slug))
    live = len(L.live_runs())
    actions = []
    for T in cfg.tracks.values():   # the test server runs staging: one deploy per staging tree
        tree = L.ref_tree(T.name, STAGING) if T.upstream and "deploy" in T.recipes else None
        if tree:
            s = job_due(C, "deploy", f"{tree}:{T.recipes['deploy']}")
            if s and s.kind == "deploy" and L.jobs_in_flight("deploy"):
                s = Step("wait", "a deploy is running")
            if s and s.kind != "wait":
                actions.append(Action(f"{T.name}:staging", s))
    for c in open_:
        if cfg.hold and TIERS.index(tier[c.slug]) > TIERS.index(cfg.hold):
            continue
        r = L.live_run(c.slug)
        if r:
            actions.append(Action(c.slug, Step("wait", f"run {r['id']} {r['role']} {'live' if r['started_at'] else 'listed'}")))
            continue
        s = next(C, c)
        if s.kind == "run":
            prior = L.run_for(c.slug, s.input)
            if prior:
                s = Step("wait", f"run {prior['id']} ended ({prior['end_kind']}) with this input: {s.why}")
            elif live >= cfg.agents:
                s = Step("wait", f"{cfg.agents} runs live: {s.why}")
            else:
                live += 1
        elif s.kind in ("build", "gate", "ship") and L.jobs_in_flight(s.kind, s.key.split(":")[0] + ":" if s.kind == "ship" else s.key):
            s = Step("wait", f"a {s.kind} of this {'branch' if s.kind == 'ship' else 'key'} is running")
        actions.append(Action(c.slug, s))
    return actions
