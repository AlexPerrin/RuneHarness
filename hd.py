#!/usr/bin/env python3
"""hd: the v8 harness. One loop over five nouns: change, tree T, judgment, target, run (docs/ARCHITECTURE.md).

Commands (docs/ARCHITECTURE.md, the command table):
  hd                      main: a pass, then the view (spawns, cards, questions, runs, goals, change facts)   R7
  hd new <slug> ...       a planning run or the user: writes a definition                                       R1
  hd show <slug>          agents: definition, contract, every verdict, gate and build result, the hand-off      R3
  hd handover <slug>      dev: reads the pushed dev ref, runs every script row, records {head, T}               R3 R8
  hd verdict <slug> <head> <rows.json>   qa: every row pass or fail, appended                                   R3
  hd ask <slug> <text>    agents: refused while a question is open on the change                                R5
  hd answer <slug> <text> main: appends a contract row                                                          R3
  hd approve <slug> <head>  main after the user's yes: approval bound to head and the PR body digest             R4
  hd tick [--dry-run]     the timer and the hook: one pass                                                      R2 R5 R6

Skeleton: every function below states what it reads, what it returns and the requirement it serves. Bodies come
one requirement at a time, each with its test class in tests/test_hd.py.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # tests point HD_ROOT at a sandbox
STATE, EVID, DEFS, TRACKS = ROOT / "state", ROOT / "evidence", ROOT / "harness", ROOT / "tools"


# ---------------------------------------------------------------- facts (P1: an unknown fact is None, never False)
class Facts:
    """Every read of the outside world. Tests replace it with a dict-driven fake. Memoised per pass."""

    def fetch(s, clone, remote):            # bool
        ...

    def rev(s, clone, ref):                 # sha | '' (no such ref) | None (unknown)
        ...

    def contains(s, clone, tip, sha):       # bool | None
        ...

    def tree(s, clone, commit):             # tree sha | None
        ...

    def merge(s, clone, base, head):        # ('ok', commit) | ('conflict', detail) | None   R8
        """git merge-tree --write-tree; the merged tree made a commit with fixed author and dates, so the same inputs
        give the same commit. The commit is what a build copy checks out; its tree sha is the key of every artefact."""
        ...

    def blob(s, clone, ref, path):          # blob sha | None   (the upstream rule files' versions on the contract)
        ...

    def pr(s, repo, owner, branch):         # {number, state, draft, head, merged, title, body} | {} | None
        ...

    def pr_checks(s, repo, number, sha):    # 'success' | 'failure' | 'pending' | 'none' | None
        ...

    def pr_comments(s, repo, number):       # [{id, author, bot, body, at, kind}] | None  (maintainer findings)
        ...

    def release(s, repo, tag):              # {tag} | {} | None
        ...

    def containers(s):                      # {name: state} | None   (docker unreachable → None → alert)
        ...

    def alive(s, pid, start):               # bool: a pid with its start time, so a recycled pid is dead
        ...

    def spawn(s, args, log, env):           # (pid, start): a detached track script, its output to the log
        ...

    def run(s, args, cwd, env):             # (rc, output): a contract script row, run inline by `hd handover`
        ...


# ---------------------------------------------------------------- what is stored (P2) and nothing else
def change(slug):
    """harness/changes/<slug>.md: front matter {slug, track, kind, priority, deps, goal, pr, finding, network, version} + body."""


def goal(slug):
    """harness/goals/<slug>.md: {slug, track, target, measure} + body."""


def contract(slug):
    """evidence/<slug>/contract.md → {hash, rules: {file: blob}, agreed, rows: [{id, text, check | gate | judge}]} | None.
    Rows `- id | text | check: <cmd>` run at hand-over and gate; `gate: <cmd>` at the gate only; `judge: <skill>` by qa with that skill."""


def seed_rows(track):
    """The '## Seed rows' section of the track's tools/track.md: the rows every contract of the track starts from."""


def record(slug, name):
    """state/<slug>/<name>.json → dict | None.  handover {head, T}; build {T, ok, detail}; gate {T, ok, detail};
    approval {head, body}; ask {text}; measure {tree, value, report}; state {state}; proc-<script> {pid, start}."""


def put(slug, name, obj):
    """Atomic write of a record with its ts."""


def verdicts(slug):
    """state/<slug>/verdicts.jsonl → [{ts, head, contract, rows: {id: 'pass' | 'fail: note'}, run}], appended only."""


def runs():
    """state/runs/*.json → [{name, role, change, step, input, brief, console_pid, console_start, agent_id, transcript,
    listed, started, ended, record, last, usage}]."""


def event(**fields):
    """One line in state/events.jsonl, only on a state change (R6), and a touch of state/wake (the watch main waits on)."""


# ---------------------------------------------------------------- the five nouns, derived
TRACK = {  # derived, not configured: the repo, the dev ref of a change, the public act that needs the user. The track's
    # script is <repo>/tools/track.sh (the fork's on its tools branch, checked out at <repo>/.worktrees/harness).
    "client": {"repo": "client", "dev": "client/{slug}", "public": "release"},
    "server": {"repo": "fork", "dev": "dev/{slug}", "public": "upstream"},
    "harness": {"repo": "harness", "dev": "harness/{slug}", "public": None},
}


class Ctx:
    """One pass's view: config, definitions, runs, and memoised facts. Clones are the harness's own under work/repos/<repo>,
    made on first use; a track's base is its repo's default branch (origin/HEAD; the server's: upstream main)."""

    def head(s, ch):
        """The change's commit: the tip of its dev ref; a release: the base tip.  '' absent, None unknown."""

    def base(s, ch):
        """The track's base tip: upstream main (server), origin/main (client), main (harness)."""

    def T(s, ch, head):
        """R8: base + each dependency's head not yet in base + head, merged in order → ('ok', commit) | ('conflict', detail) | None."""

    def live(s, ch, head):
        """A6: the target holds head. client: master; server: state/live/tree.json's heads; harness: main."""

    def done(s, ch, head):
        """A6: a server change when upstream main holds head; every other change when live."""

    def alive_run(s, ch):
        """The run of this change that has not ended, if any."""

    def start(s, slug, name, args, env):
        """R5: start a track script once (pid + start time recorded); one that died twice without its result is raised once."""


def nxt(ctx, ch):
    """The first unmet step (docs/ARCHITECTURE.md, The loop). Returns {state: a fact in words (R7), actor, input, detail, act}.

    deps live?                 no → wait
    contract agreed?           no → seed rows written (script); server: qa run (mode contract)
    hand-over at the dev tip?  no → dev run (mode code; a hand-off file lists the successor)
    T                          conflict → dev
    build(T)                   none → tools/track.sh build; failed → dev
    gate(T)                    none → tools/track.sh gate; failed → dev
    verdict(head, contract)    none, or the rule files' blobs moved → qa (mode judge); failed code rows → dev
    server: live on the test server?   no → ship-test (the pass's integration step)
    public act?                approval at head? no → card (user)
    ship                       upstream: hd-public; release: hd-public; else tools/track.sh ship
    wait                       upstream merged → done
    """


def integration(ctx):
    """T_int: upstream main + the permanent pins + every gated open server head whose deps are live, merged in order.
    On a conflict a recorded fork ref local/merge/<a7>-<b7> stands in for both heads; else the younger change's dev.
    → {commit, tree, heads, names} | {conflict, change, detail, with} | None."""


def brief(ctx, ch, st, run_name, role):
    """state/briefs/<run>.md: role and mode, the paths (clone, build copy, evidence, contract), the state and why,
    the predecessor's hand-off, the last verdict's rows, the definition, the contract, the one-line hand-back."""


def dispatch(ctx, ch, st, act):
    """R2 R6: list a run for an unmet agent step when no run of the change is alive, no question is open, no ended run
    has the same input without a hand-off, and fewer than cfg.agents runs are alive or listed. Writes the run and brief."""


def repairs(ctx, act):
    """R5: end runs whose console pid is gone; bring down a change's server with no run alive; docker or gh down → one alert."""


def measure(ctx, g, act):
    """R1: the goal's measure script runs when the target's tree (client: master + the live server tree) differs from
    measure.json's; below target with no open change serving the goal, a planning dev run is listed."""


def tick(ctx=None, act=True):
    """One pass under the state lock: repairs → goals → every open change (nxt; act on scripts; dispatch agents; cards;
    the integration tree and its deploy) → an event per change whose state changed → the view for `hd`."""


def card(ctx, ch, st):
    """The user's card: head, verdict rows, PR title, body and comment (or the release), and the approve command."""


# ---------------------------------------------------------------- commands (refusals list every reason at once)
def cmd_show(args): ...
def cmd_handover(args): ...     # refuses: no agreed contract; dev ref missing or unknown; evidence empty; T conflict; any script row failing
def cmd_verdict(args): ...      # refuses: head moved; a contract row missing; a value not 'pass' or 'fail: note'
def cmd_ask(args): ...          # refuses: a question already open on the change
def cmd_answer(args): ...       # appends `- answer-N | <ts> the user: <text> | judge`, drops the question
def cmd_approve(args): ...      # refuses: the change is not at its user step for that head; records {head, body digest}
def cmd_new(args): ...
def cmd_tick(args): ...


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
