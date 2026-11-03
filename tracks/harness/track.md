# Harness track

Changes to this repo. The pass creates your worktree `.worktrees/<slug>` on branch `harness/<slug>` from the live
branch; the dev ref stays local. A test per requirement touched; decide.py is tested over ledger snapshots, never
fakes. Run `python3 -m unittest discover -s tests` yourself, commit, then `hd submit <slug>`: the pass gates the
candidate (tests, replay) and ships it by fast-forward of the live branch.

The replay runs the candidate's `hd tick --dry-run --offline` over a snapshot of the live ledger against the live
one. A change that must plan differently (a new guard, a changed reason text) writes `evidence/<slug>/replay.md`
saying what differs and why; the replay then passes with that note.

## Seed criteria
- tests  | the suite passes at the candidate | script: python3 -m unittest discover -s tests
- replay | the candidate pass over a snapshot of the live ledger plans what the live pass plans, or evidence/<slug>/replay.md explains the difference | script: bash tracks/harness/replay.sh
