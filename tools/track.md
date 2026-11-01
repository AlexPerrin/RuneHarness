# Harness track

Changes to this repo (hd.py, hook.py, hd-public, tools/, roles, the drive skill, docs, tests). Branch `harness/<slug>` from the live checkout's branch (the brief's Base) in
the worktree `.worktrees/<slug>`; one test per requirement touched (`tests/test_hd.py`, one class per R); docs state current
truth only; CLAUDE.md and README.md are the only root docs. Hooks live in `.claude/settings.json`. A change to an
upstream-acting step is dry-run against the live PRs before it merges (`hd tick --dry-run` must plan nothing main's
pass does not). Push the branch, then `hd handover <slug>`.

## Seed rows
- tests | the suite passes at T | gate: tools/track.sh check-tests
- dry-run | hd tick --dry-run at T plans no upstream action main's pass does not | gate: tools/track.sh check-dry-run
- docs | every requirement has its test class and acceptance row | gate: tools/track.sh check-docs
