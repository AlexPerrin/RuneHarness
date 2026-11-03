---
slug: harness-handoff-commits-wip
track: harness
title: A context-limit hand-off leaves the run's work committed and pushed
kind: change
priority: P1
deps: []
created: '2026-11-01T04:59:09Z'
---
quest-runemysteries-2, -3, -4 and harness-desktop-token-login-1 each hit the context limit and handed off with their code uncommitted in the change's clone (runemysteries-4: three rewritten files and a new projectile, never compiled). The next run inherits a dirty worktree, and a removed or reset worktree loses the work. Expected: when the PostToolUse context limit tells a run to hand off, the run commits its work in progress to the change's dev branch and pushes it to the fork before it writes handoff.md, and the next brief names that commit. Also: a run that reaches the limit three times on one change without a handover is a signal hd surfaces (the change is too large for one run, or the brief spends context on reading). One test per requirement touched.
