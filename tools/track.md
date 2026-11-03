# Harness track

Changes to this repo. Branch `harness/<slug>` from the live branch in the worktree `.worktrees/<slug>`; the dev ref
stays local. A test per requirement touched; decide.py is tested over recorded ledger snapshots, never fakes.
Docs hold one fact per line (`tools/docfmt.py`), so parallel doc edits merge. Commit, then
`hd handover <slug> Limits: none` (or `Limits: limit:<slug> ...`, each a change filed with `hd new --blocks`).

## Seed rows
- tests  | the suite passes at T                                              | check: tools/track.sh test
- replay | the candidate pass over a snapshot of the live ledger plans what the live pass plans, or a row names the difference | gate: tools/track.sh gate replay
- docs   | the source docs hold one fact per line                              | gate: python3 tools/docfmt.py --check docs/*.md
- tools  | every carried tools head fast-forwards its branch and its tests pass | gate: tools/track.sh gate tools
