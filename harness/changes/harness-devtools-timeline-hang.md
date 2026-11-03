---
slug: harness-devtools-timeline-hang
track: harness
title: A devtools data call returns or fails; get_timeline never hangs
kind: change
priority: P0
deps: []
created: '2026-11-01T13:46:20Z'
---
Hand-back of cannon-354-reset-ammo-varp-2 (2026-11-01): a get_timeline call on the desktop devtools hung for 30 minutes; the desktop was logged out for idling meanwhile and the run hit its context limit mid-proof, leaving the in-game state unknown (evidence/cannon-354-reset-ammo-varp/handoff.md). A hung data call stalls a run with no fact to act on. Acceptance: get_timeline (and every devtools data tool) returns or returns an error on an observed fact (the client thread answered or the client is gone), never blocks indefinitely; a test reproduces the hang's cause.
