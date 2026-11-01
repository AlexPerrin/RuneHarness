# Harness track

Changes to this repo (hd.py, hook.py, hd-public, tools/, roles, the drive skill, docs, tests). Branch `harness/<slug>` from the live checkout's branch (the brief's Base) in
the worktree `.worktrees/<slug>`; one test per requirement touched (`tests/test_hd.py`, one class per R); docs state current
truth only; CLAUDE.md and README.md are the only root docs. Hooks live in `.claude/settings.json`. A change to an
upstream-acting step is dry-run against the live PRs before it merges (`hd tick --dry-run` must plan nothing main's
pass does not). The dev ref stays local, as does each carried tools ref: hd reads the local ref and ship pushes only
the live branch and the tools branches it moves, so rebase it onto the base at will and never push it. Commit, then `hd handover <slug>`.

A fix to a product repo's tools (the fork's `local/harness`, the client's `client/harness-v8`) is committed on branch
`harness/<slug>` of that repo, from its tools branch, in a worktree `<repo>/.worktrees/<slug>`; the dev ref
`harness/<slug>` of this repo exists too (at the live branch when nothing here changes). The hand-over records each carried
head; the gate runs that repo's `tools/**/test_*.py` at it; ship fast-forwards the tools branch to it and pushes it to that repo's own remote (the fork's `fork`, never `origin`).

## Seed rows
- tests | the suite passes at T | gate: tools/track.sh check-tests
- dry-run | hd tick --dry-run at T plans no upstream action main's pass does not | gate: tools/track.sh check-dry-run
- docs | every requirement has its test class and acceptance row | gate: tools/track.sh check-docs
- tools | every carried tools head is a fast-forward of its branch and its tests pass | gate: tools/track.sh check-tools
