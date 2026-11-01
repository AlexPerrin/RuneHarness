---
slug: harness-stale-rework-leftovers
track: harness
title: Remove what today's reworks left stale
kind: change
priority: P1
deps: []
created: '2026-11-01T21:17:41Z'
---
Found by the read-only monitor sweep (2026-11-01 ~21:12Z) the user asked for. CLAUDE.md lists hd-public (gone) and an hd command list without close, stop, rows, tree; state/seen.orchestrator.json keeps a 'message' key (hd tell is gone); state/goblin-diplomacy-review-367-fftgsrq/ship.json says 'ready for review' though the user returned #367 to draft at 20:46:38Z. Acceptance: CLAUDE.md states the current files and commands; seen.orchestrator.json has no dead keys; a ship record that GitHub contradicts is not trusted (or is cleared); a test covers the last.
