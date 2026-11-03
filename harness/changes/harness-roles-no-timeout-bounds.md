---
slug: harness-roles-no-timeout-bounds
track: harness
title: Runs started after the facts rule still time-bound steps with timeout
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T06:46:45Z'
---
Monitor sweep 48 P2-b: card-run-blank-1 ran `timeout 600 tools/track.sh test` (06:36:34Z) and endpoint-owner-2 `timeout 20 python3 -m unittest` (06:38:13Z), both started after roles-wait-on-facts shipped (06:22Z). Acceptance: the role texts (or the hook) leave no time bound on a step; a run's step ends on its observed outcome.
