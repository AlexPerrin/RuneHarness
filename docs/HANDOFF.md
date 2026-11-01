# HANDOFF

The brief for a fresh session. `~/osrs-harness` has branch `v8` checked out; `main` still holds v7 (its timer is
stopped, its state under `harness/state`). v8 runs from here; the merge into `main`, the timer and the sudoers line
are the cutover the user approves.

## Start (one session, in ~/osrs-harness on branch `v8`)
Its `.claude/settings.json` wires v8's hooks and its `.claude/agents/` holds the roles; a session started elsewhere
binds no run. The driver and the user's chat: `cd ~/osrs-harness && claude --agent orchestrator`, told "drive": it
arms the watch on `state/wake.orchestrator`, runs `python3 hd.py`, spawns each listed run, handles hand-backs, shows cards,
questions and alerts and acts on the user's words; the user types the yes and the close themselves
(`! python3 ~/osrs-harness/hd.py approve <slug> <head>` / `close <slug> <text>`). The planner run the pass lists monitors operations and files harness changes for the issues it finds; a harness change goes through the same
loop (a dev run in `~/osrs-harness/.worktrees/<slug>`, the gate's tests, a fast-forward of `v8`).
`python3 -m unittest discover -s tests` must stay green. The track scripts live in the product repos: the fork's branch
`local/harness` (worktree `~/src/OpenRune-Server/.worktrees/harness`) and the client's branch `client/harness-v8`
(worktree `~/osrs-plugins-reverse/.worktrees/harness-v8`), each with its own tests; both are local, unpushed.
Commits pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the
Co-Authored-By line only. Never leave uncommitted edits in ~/osrs-harness.

## Before the first server change gates
`pins` in hd.yaml is empty. The integration tree is upstream main plus the pins plus the gated heads, so the first
test-server deploy would drop every branch v7 carried (40: `local/*`, `fin/*`, `fix/*`, listed in v7's
`integration.txt` on the fork's `local/integration-tools`). Fill `pins` with the branches the test server must keep,
or file each as a change, before any server change passes its gate.

## What is built and what is not
Built with tests: the loop (`hd.py`, every requirement's class), the hook, `hd-public`, the three track scripts, the
server's check rows (`gamevals.py`, `text.py`), the client's check rows. `python3 hd.py tick --dry-run` runs against the
real repos and v7's definitions.
Not yet run for real: a server `build`, `up`, `gate-ci` and `ship`; a client `build`, `up` and `measure`; `hd-public`
against a PR. Each acceptance row in docs/ACCEPTANCE.json stays `false` until its live check runs.

## Cutover, in order
1. The user: a fine-grained token limited to AlexPerrin/* for `gh`; Unix user `hd` with the full token and the sudoers
   line (docs/ARCHITECTURE.md, Run and test); the `pins` list in hd.yaml; the `fix/31` decision.
2. The sidecar's data dir: `SIDECAR_DATA` (default `~/src/openrune-work/server-tools/sidecar/data`, v7's tools
   branch) until it moves onto `local/harness`.
3. Regenerate the RSProx text transcripts with every packet filter on (`tools/track.sh recordings` reads them).
4. Stop v7's timer, merge `v8` into `main`, install the units, resume with `claude --agent orchestrator`.
