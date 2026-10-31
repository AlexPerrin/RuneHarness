# HANDOFF

The brief for a fresh session on branch `v8`. v7 runs on `main` with its pass paused (`harness/state/paused` in
`~/osrs-harness`); v8 is built in the worktree `~/osrs-harness-v8` and goes live only when the user approves the
cutover (merge into `main`, the timer and the sudoers line installed).

## Start prompt
Start in ~/osrs-harness-v8 on branch `v8`. Read CLAUDE.md, docs/PROBLEM.md, docs/PRD.md, docs/ARCHITECTURE.md and
docs/ACCEPTANCE.json, then docs/ISSUES.md. `python3 -m unittest discover -s tests` must pass. The track scripts live in
the product repos: the fork's branch `local/harness` (worktree `~/src/OpenRune-Server/.worktrees/harness`) and the
client's branch `client/harness-v8` (worktree `~/osrs-plugins-reverse/.worktrees/harness-v8`); each has its own tests.
Commits pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the
Co-Authored-By line only. Never leave uncommitted edits in ~/osrs-harness.

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
4. Stop v7's timer, merge `v8` into `main`, install the units, resume with `python3 hd.py` from the user's chat
   (skill `head`).
