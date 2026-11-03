# Harness track

Changes to this repo. Branch `harness/<slug>` from the live branch in the worktree `.worktrees/<slug>`; the dev ref
stays local. A test per requirement touched; decide.py is tested over recorded ledger snapshots, never fakes. Run
`tracks/harness/track.sh gate <slug>` yourself, commit, then `hd handover <slug>`.

## Seed rows
- tests  | the suite passes at T | script: tracks/harness/track.sh test
- replay | the candidate pass over a snapshot of the live ledger plans what the live pass plans, or a row names the difference | script: tracks/harness/track.sh gate replay
