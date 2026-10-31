# HANDOFF

The brief for a fresh session on branch `v8`. v7 runs on `main` (its pass is paused: `harness/state/paused`); v8 is
built here, in the worktree `~/osrs-harness-v8`, and goes live only when the user approves the cutover.

## Start prompt
Start in ~/osrs-harness-v8 on branch `v8`. Read CLAUDE.md, docs/PROBLEM.md, docs/PRD.md, docs/ARCHITECTURE.md and
docs/ACCEPTANCE.json (the design, approved by the user on 2026-10-31), then docs/V8-BRIEF.md §0–§4 for the measured
evidence and docs/ISSUES.md. The user's go for the implementation is given. Build one requirement at a time, each with
its test class in tests/test_hd.py, flipping its row in docs/ACCEPTANCE.json only after its check command passes.
Measure against docs/V8-BRIEF.md §3 with the scripts in ~/osrs-harness/evidence/monitor/ (git-ignored, main checkout).
Commits pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the
Co-Authored-By line only. Never leave uncommitted edits in ~/osrs-harness (main's working tree).

## Decisions taken with the user (2026-10-31)
- Gate bound to T; verdict and approval bound to head + contract; rule rows carry the upstream rule files' blob shas.
- Main spawns, woken by a watch re-armed on every wake; the pass never spawns.
- Only the public act runs as Unix user `hd` through one sudoers-limited helper; everything else as the user with a
  token limited to AlexPerrin/*.
- Server contract written by a qa run before code; client and harness contracts derived.
- A maintainer finding files a new change on the same PR, contract inherited plus the finding's row.
- No integrator, no orchestrator roles: a pin conflict is the younger change's dev (merge ref against a permanent
  pin); planning is a dev brief.
- Runs hand off at 150–200k context (cost, not quality).

## Waits on the user (docs/V8-BRIEF.md §0a plus)
Mirrored WSL networking (done at this restart), the fine-grained token and the `hd` user with the sudoers line, the
`fix/31` decision, the jav_config privacy change. Before the first server contract: regenerate the RSProx text
transcripts with every packet filter on (0 of 151 hold clan or friend-list packets).

## Unconfirmed measurements (from the monitor, to carry into docs/ISSUES.md)
The 131-module recompile after adding a pack module; why every SubagentStop hook was cancelled; that the binary
RSProx recordings hold clan packets; fixed-mode login coordinates as the cause of the login stall; no Jagex contact
from the desktop jav_config (RSProx logs only, no capture).
