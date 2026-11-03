"""ledger → Step: next(change) and the pass's plan (docs/ARCHITECTURE.md §3).

Pure: takes a Ledger and parsed definitions; no subprocess, no network, no clock. Tested over recorded ledger
snapshots (tests/fixtures/), never over fakes of git or GitHub.
"""
from dataclasses import dataclass, field

from store import Ledger


@dataclass(frozen=True)
class Change:
    """A parsed harness/changes/<slug>.md front matter + body."""
    slug: str
    track: str              # client | server | central | filestore | harness
    kind: str               # change | release
    upstream: bool = True   # False: fork only, never a PR
    priority: str = "P2"    # P0..P4
    deps: tuple = ()
    goal: str = ""
    units: tuple = ()
    pr: int = 0
    branch: str = ""
    body: str = ""


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
class Cfg:
    agents: int = 7
    hold: str = ""          # the held band, e.g. "P2": nothing below it runs
    tracks: dict = field(default_factory=dict)


DONE = Step("done", "done")


# --- guards: each returns a Step or None; first non-None wins ---------------------------------------------------

def closed(L: Ledger, ch: Change):
    """change_state.closed_at or folded_into → done."""
    raise NotImplementedError


def deps_live(L: Ledger, ch: Change):
    """every dep: landed(dep, dep's target) or closed; else wait naming the dep."""
    raise NotImplementedError


def ask_open(L: Ledger, ch: Change):
    """an ask with no answer → wait (the question)."""
    raise NotImplementedError


def criteria_due(L: Ledger, ch: Change):
    """an upstream change with no run(mode=criteria) whose record is 'criteria agreed' → run qa/criteria."""
    raise NotImplementedError


def dev_due(L: Ledger, ch: Change):
    """no submission at ref(dev tip), or criteria created after submission.at, or last verdict at head FAIL, or a recorded
    merge conflict / CI failure / missing text at head → run dev/code with the reason as input."""
    raise NotImplementedError


def build_due(L: Ledger, ch: Change):
    """job(build, key(candidate)) missing or ok NULL → build; ok 0 → run dev."""
    raise NotImplementedError


def gate_due(L: Ledger, ch: Change):
    """job(gate, key(candidate)) missing or ok NULL → gate; ok 0 → run dev (check_result rows name the failures)."""
    raise NotImplementedError


def judge_due(L: Ledger, ch: Change):
    """judged criteria and no verdict(head, digest(judged criteria)) → run qa/judge; verdict ok 0 is dev_due's."""
    raise NotImplementedError


def stage_due(L: Ledger, ch: Change):
    """server tracks: head not an ancestor of ref staging → merge (act.stage)."""
    raise NotImplementedError


def upstream_dep_wait(L: Ledger, ch: Change):
    """a dep with its own PR not landed(upstream main) → wait; its card held by the user → alert."""
    raise NotImplementedError


def texts_due(L: Ledger, ch: Change):
    """pr-comment.md misses commits since the PR's live head, or a finding has no reply file → run dev."""
    raise NotImplementedError


def card_due(L: Ledger, ch: Change):
    """no card(change, head, digest(steps, texts)) → card."""
    raise NotImplementedError


def approval_wait(L: Ledger, ch: Change):
    """card shown, no approval: hold → wait (hidden); else wait (the user)."""
    raise NotImplementedError


def publish_due(L: Ledger, ch: Change):
    """approval not spent and a publish_step undone → publish."""
    raise NotImplementedError


def published_wait(L: Ledger, ch: Change):
    """every step done and not landed(upstream main) → wait (maintainers)."""
    raise NotImplementedError


def ship_due(L: Ledger, ch: Change):
    """harness/client: not landed(live branch) → ship (serial: one job(ship) in flight per track)."""
    raise NotImplementedError


def measure_due(L: Ledger, ch: Change):
    """a goal whose target tree moved since measure.tree → measure."""
    raise NotImplementedError


def plan_due(L: Ledger, ch: Change):
    """a goal below target with no open change naming it → run dev/plan on the goal's track."""
    raise NotImplementedError


GUARDS = [
    closed, deps_live, ask_open, criteria_due, dev_due, build_due, gate_due, judge_due, stage_due,
    upstream_dep_wait, texts_due, card_due, approval_wait, publish_due, published_wait, ship_due, measure_due, plan_due,
]


def next(L: Ledger, ch: Change) -> Step:
    for guard in GUARDS:
        step = guard(L, ch)
        if step:
            return step
    return DONE


def priority(ch: Change, blocked: dict) -> str:
    """min tier over {ch} ∪ the open changes ch blocks; a harness change is P1 at least."""
    raise NotImplementedError


def plan(L: Ledger, changes: list, cfg: Cfg) -> list:
    """The pass's action list (ARCHITECTURE §3): next() per open change in priority order (harness, PR rounds, new content;
    below cfg.hold → skip); a run Step listed only while live runs < cfg.agents and no run exists for
    (change, input); a script Step only while no job of its key is in flight; a card only when not shown."""
    raise NotImplementedError
