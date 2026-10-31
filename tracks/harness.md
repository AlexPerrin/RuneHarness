# Harness track

Changes to this repo (hd.py, hook.py, tracks/, roles, skills, docs, tests). Branch `harness/<slug>` in a worktree
`~/src/work/<slug>`; one test per requirement touched (`tests/test_hd.py`, one class per R); docs state current
truth only; CLAUDE.md and README.md are the only root docs. Hooks live in `.claude/settings.json`. A change to an
upstream-acting step is dry-run against the live PRs before it merges (`hd tick --dry-run` must plan nothing main's
pass does not). Push the branch, then `hd handover <slug>`.

## Seed rows
- tests | the suite passes at T | check: python3 -m unittest discover -s tests
- dry-run | hd tick --dry-run at T plans no upstream action main's pass does not | check: tracks/harness.sh check-dry-run
- docs | every requirement touched has its test class | check: tracks/harness.sh check-docs
