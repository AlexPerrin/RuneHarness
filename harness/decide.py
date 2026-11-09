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
    priority: str = "P2"    # P0..P4
    deps: tuple = ()
    goal: str = ""
    units: tuple = ()
    feature: str = ""       # the user's PR bundle: the fork branch the feature's PRs are opened from (feat/<x>, content/<x>)
    members: tuple = ()     # a package (decide.packages): the member changes of its feature on its track, in dependency order
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

    def candidate_base(self, ch=None):
        """The ref a candidate starts from: staging on a track that deploys the test server (proved on what the server
        runs, H4), else base; a package is self-contained on base (G4)."""
        return STAGING if self.upstream and "deploy" in self.recipes and not (ch and ch.members) else self.base

    def done_ref(self, ch):
        """Where a landed row means done: the live branch, upstream main for a package, staging for a change."""
        return self.base if (not self.upstream or ch.members) else "refs/heads/staging"


@dataclass(frozen=True)
class Cfg:
    agents: int = 7
    builds: int = 3
    hold: str = ""          # the held band, e.g. "P2": tiers below it do not run
    free: int = 0           # GB: below it on a build disk, no build starts (observe.disk alerts)
    tracks: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Step:
    kind: str               # done|wait|run|withdraw|build|gate|rerun|alert|merge|card|publish|ship|measure|release
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
    """<T>:<recipe> (built); a gate's T carries _h<head tree12> where the head's tree is not the candidate's: the gate
    also tests the PR (the head on base: CI, spotless), so two heads of one candidate tree are gated each."""
    h = s["head_tree"] if "head_tree" in s.keys() else None
    t = built(s) + (f"_h{h[:12]}" if kind == "gate" and h and h != s["tree"] else "")
    return f"{t}:{C.cfg.tracks[ch.track].recipes.get(kind, '')}"


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
    """A change is done when closed, or landed on staging and live on the test server (on a track without staging:
    its head's verdict ok; off the server tracks: landed on the live branch). A package is done when landed on
    upstream main, or closed with its feature, or when no member is left open."""
    T = C.cfg.tracks[ch.track]
    if C.L.closed(ch.slug):
        return True
    if ch.members:
        return bool(C.L.landed(ch.slug, T.base) or C.L.closed(ch.feature) or all(C.L.closed(m) for m in ch.members))
    if not T.upstream:
        return bool(C.L.landed(ch.slug, T.base))
    if stages(C, ch):
        return bool(C.L.landed(ch.slug, STAGING) and C.L.landed(ch.slug, "live"))
    t = tip(C, ch)
    v = C.L.last_verdict(ch.slug, t) if t else None
    return bool(v and v["ok"])


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
    if not (T.upstream and ch.feature and not ch.members):   # a change headed upstream: its accuracy before code
        return None
    if C.L.runs_with_record(ch.slug, "criteria", "criteria agreed"):
        return None
    return Step("run", "criteria before code", role="qa", mode="criteria", input=digest("criteria", ch.slug))


def judged_digest(C, ch):
    return digest([(c["rid"], c["text"]) for c in C.L.criteria(ch.slug, "judge")])


def outdated(C, ch, v) -> bool:
    """A FAIL verdict over another criteria set (a waiver since) or older than a dep's landing: what it failed on may be
    gone, so the head is judged again before a dev re-runs."""
    if not v or v["ok"]:
        return False
    if v["criteria_digest"] != judged_digest(C, ch):
        return True
    at = [C.L.one("SELECT max(at) a FROM landed WHERE change=?", d)["a"] for d in ch.deps]
    return any(x and x > v["at"] for x in at)


def failed(kind, detail) -> str:
    """What a failure names: a gate's failing criteria ('rid (note); rid (note)' → the rids), else the whole detail."""
    return ",".join(sorted(p.split(" (")[0] for p in detail.split("; "))) if kind == "gate" else detail


def dev_due(C, ch):
    """A dev only for what the head can fix: a build, gate or ship failure first runs once more at the same head; the
    same failure again is the head's (dev), a different one is outside it (alert, no dev)."""
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
        for kind, k in (("build", key(C, ch, "build", s)), ("gate", key(C, ch, "gate", s)),
                        ("ship", f"{C.cfg.tracks[ch.track].base}:{s['tcommit']}")):
            j = C.L.job(kind, k)
            if not (j and j["ok"] == 0):
                continue
            first = C.L.rerun(ch.slug, kind, k)
            if first is None:   # the head is not known to be at fault until the failure repeats on it
                return Step("rerun", f"{kind} failed: {j['detail']}; once more at the same head", key=f"{kind} {k}")
            if failed(kind, first) != failed(kind, j["detail"] or ""):   # it moved without the head moving: outside the head
                return Step("alert", f"{kind} {short(k)} failed twice, differently: {first} / {j['detail']}", key=f"{kind}:{k}")
            why.append(f"{kind} failed twice: {j['detail']}")
        e = C.L.last_event(ch.slug, "merge-conflict") if stages(C, ch) else None
        if e and e["detail"].split()[:2] == [t[:7], (C.L.ref(C.cfg.tracks[ch.track].name, STAGING) or "")[:7]]:   # a moved staging is merged again first
            why.append(f"merge conflict on staging: {e['detail']}")
        e = C.L.last_event(ch.slug, "ci-failed")
        if e and e["detail"].startswith(t[:7]):
            why.append(f"CI failed at {t[:7]}: {e['detail'][8:]}")
        if ch.members:
            m, e = members_digest(C, ch), C.L.last_event(ch.slug, "packaged")
            if not e or e["detail"].split()[0] != m:
                why.append(f"members moved since the package ({m[:12]})")
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
    d = judged_digest(C, ch)
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
    return bool(T.upstream and not ch.members and ("deploy" in T.recipes or ch.track in LIBRARY))


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


def live_wait(C, ch):
    """On staging, not yet run by the test server: the deploy is the pass's (one per staging tree)."""
    return Step("wait", "not yet live on the test server") if stages(C, ch) and not C.L.landed(ch.slug, "live") else None


# --- features: a change names its PR bundle by `feature:`; one package per (feature, upstream track) ---------------

def pkg_slug(feature, track) -> str:
    return f"pr-{feature.replace('/', '-')}-{track}"


def packages(defs, tracks) -> list:
    """A Change per (feature, track with an upstream): its members in dependency order, its tier their best. Its dev
    ref holds the package (upstream main or the published PR head, plus the members' commits: `hd package`)."""
    by = {}
    for c in defs:
        if c.feature and not c.members and c.track in tracks and tracks[c.track].upstream:
            by.setdefault((c.feature, c.track), []).append(c)
    out = []
    for (f, t), ms in sorted(by.items()):
        get = {m.slug: m for m in ms}.get
        order = []
        def walk(m):
            for d in m.deps:
                if get(d) and d not in order:
                    walk(get(d))
            if m.slug not in order:
                order.append(m.slug)
        for m in sorted(ms, key=lambda m: m.slug):
            walk(m)
        slug = pkg_slug(f, t)
        out.append(Change(slug, t, priority=min((m.priority for m in ms), key=TIERS.index), feature=f, members=tuple(order),
                          title=f"PR {f} on {tracks[t].upstream}", body=PACKAGE_BODY.format(slug=slug, feature=f, track=t, members="\n".join(f"- {m}" for m in order))))
    return out


PACKAGE_BODY = """# PR {feature} on {track}

The package of feature `{feature}`: upstream main (or the PR's published head) plus the members' commits in dependency
order, never squashed. In your clone run `hd package {slug}`: it applies every member commit the branch lacks; on a
conflict resolve it, `git cherry-pick --continue` and run it again; then push and `hd submit {slug}`. Write
evidence/{slug}/pr-title.txt and pr-body.md (upstream's template) for a new PR, and pr-comment.md covering the net change
since the PR's published head, each true of the package's net diff. A code defect (CI, a failing verdict, a finding) is
fixed in a member, never here: `hd new <slug> --track {track} --feature {feature} ...`, then hand back `filed <slug>`.

Members:
{members}
"""


def members_digest(C, P) -> str:
    """The open members and their heads: a package is made again when it moves."""
    return digest([(m, tip(C, C.defs[m])) for m in P.members if m in C.defs and not C.L.closed(m)])


def members_wait(C, P):
    """Every open member live on staging before its package; a member's same-track dep outside the feature must be
    merged upstream first (G4: the PR holds no other PR's commits nor a fork-only one)."""
    T = C.cfg.tracks[P.track]
    for m in P.members:
        ch = C.defs.get(m)
        if ch is None or C.L.closed(m):
            continue
        if not done(C, ch):
            return Step("wait", f"member {m}: {next(C, ch).why}")
        for dep in ch.deps:
            d = C.defs.get(dep)
            if not d or d.track != P.track or d.feature == P.feature or C.L.closed(dep):
                continue
            if not d.feature:
                return Step("wait", f"member {m} depends on {dep}, which names no feature: its commits reach no PR")
            if not C.L.landed(pkg_slug(d.feature, d.track), T.base):
                return Step("wait", f"member {m} depends on {dep} of {d.feature}, not yet merged upstream")
    return None


def pr_of(C, P):
    return C.L.pr_on_branch(C.cfg.tracks[P.track].upstream, P.feature)


def texts_due(C, P):
    """A package needs its texts before a card: title and body for a new PR, the comment for every head, a reply file
    per finding → run dev (text work only)."""
    t, texts = tip(C, P), C.L.texts(P.slug)
    missing = [n for n in (("pr-comment.md",) if pr_of(C, P) else ("pr-title.txt", "pr-body.md", "pr-comment.md")) if not texts.get(n, "").strip()]
    missing += [f"pr-reply-{f['comment_id']}.md" for f in C.L.findings(P.slug) if f"pr-reply-{f['comment_id']}.md" not in texts]
    if not missing:
        return None
    return Step("run", "texts: " + ", ".join(missing), role="dev", mode="code", input=digest(t, missing))


def pre_card(C, P):
    for guard in (members_wait, ask_open, dev_due, build_due, gate_due, judge_due, texts_due):
        step = guard(C, P)
        if step:
            return step
    return None


def feature_pkgs(C, feature) -> list:
    return [p for p in C.defs.values() if p.members and p.feature == feature and not done(C, p)]


def sisters_wait(C, P):
    """Sister PRs (one feature across repos) share one card: each waits until every sister is ready for it."""
    for p in feature_pkgs(C, P.feature):
        s = p.slug != P.slug and pre_card(C, p)
        if s:
            return Step("wait", f"sister {p.slug}: {s.why}")
    return None


def card_head(C, pkgs) -> str:
    """The card's head: the package's, or for sister PRs a digest of every package head."""
    heads = [tip(C, p) for p in pkgs]
    return heads[0] if len(heads) == 1 else digest([(p.slug, h) for p, h in zip(pkgs, heads)])


def held(C, feature, head, slugs):
    """A hold on the feature's card, or a standing hold (every head) on a package or member."""
    for s in slugs:
        if h := C.L.hold(s, ""):
            return h
    return C.L.hold(feature, head)


def feature_card(C, P):
    """The feature's one card, approval and publish, listed on its first open package; the sisters wait on it.
    No card at the packages' heads, its approval spent by a refusal, or texts observed since shown → card."""
    pkgs = feature_pkgs(C, P.feature)
    head, F = card_head(C, pkgs), P.feature
    c = C.L.latest_card(F)
    a = c and C.L.one("SELECT spent_why FROM approval WHERE card=?", c["id"])
    published = a and a["spent_why"] == "published" and all((pr_of(C, p) or {}).get("head") == tip(C, p) for p in pkgs)   # a sister merged since
    step = None
    if not c or c["head"] != head and not published:
        step = Step("card", f"card {F} at {head[:7]}", key=head)
    else:
        refused = a and a["spent_why"] and a["spent_why"] != "published"
        moved = any(C.L.one("SELECT 1 FROM text WHERE change=? AND at>?", p.slug, c["shown_at"]) for p in pkgs)
        if refused:
            step = Step("card", f"card {F} at {head[:7]} after a refusal", key=head, input=a["spent_why"])
        elif moved:
            step = Step("card", f"card {F} at {head[:7]}", key=head)
        elif not a:
            h = held(C, F, c["head"], [p.slug for p in pkgs] + [m for p in pkgs for m in p.members])
            step = Step("wait", f"held: card {c['id']} hidden ({h['change']})" if h else f"the user: card {c['id']} {F} at {head[:7]}")
        elif C.L.approval(c["id"]) and C.L.undone_steps(c["id"]):
            step = job_due(C, "publish", str(c["id"]))
    if step and P.slug != pkgs[0].slug:
        return Step("wait", f"{F}: {step.why} (on {pkgs[0].slug})")
    return step


def published_wait(C, P):
    return None if C.L.landed(P.slug, C.cfg.tracks[P.track].base) else Step("wait", "maintainers")


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


GUARDS = [closed, deps_live, ask_open, criteria_due, dev_due, build_due, gate_due, judge_due, stage_due, live_wait, ship_due]
PACKAGE_GUARDS = [closed, members_wait, ask_open, dev_due, build_due, gate_due, judge_due, texts_due, sisters_wait,
                  feature_card, published_wait]


def next(C, ch) -> Step:
    for guard in PACKAGE_GUARDS if ch.members else GUARDS:
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
    return p if p and p["end_kind"] not in ("console", "handoff", "withdrawn") and not (p["end_kind"] == "stop" and p["started_at"]) else None


def plan(L: Ledger, changes: list, cfg: Cfg, goals: list = ()) -> list:
    """The pass's action list: next() per open change and package in priority order (harness, then packages, then new content;
    below cfg.hold skipped); a run Step listed only while live runs < cfg.agents and no run with this input parks it
    (parked); a job Step only while no job of its key (a ship: of its branch) is in flight."""
    C = Ctx(L, cfg, {c.slug: c for c in changes})
    open_ = [c for c in changes if not L.closed(c.slug) and c.track in cfg.tracks]
    blocked = {}
    for c in open_:
        for d in c.deps:
            blocked.setdefault(d, []).append(c)
    tier = {c.slug: priority(c, blocked) for c in open_}
    open_.sort(key=lambda c: (0 if c.track == "harness" else 1 if c.members else 2, TIERS.index(tier[c.slug]), c.slug))
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
        if r and s is not DONE and not r["started_at"] and s.kind != "run":   # a listing its change no longer plans (it waits on a dep, a job, the user)
            actions.append(Action(c.slug, Step("withdraw", f"run {r['id']} withdrawn before it started: {s.why}", key=str(r["id"]))))
            live -= 1
            continue
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
