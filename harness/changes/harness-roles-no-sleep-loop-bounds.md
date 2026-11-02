---
slug: harness-roles-no-sleep-loop-bounds
track: harness
title: Bounded sleep loops pass the timeout rule
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T07:00:00Z'
---
Monitor sweep 50 P2-a: server-clan-guest-3 ran `for i in $(seq 1 17); do grep -qsE ... && break; sleep 10; done` at 06:52:36, 06:52:45 and 06:52:54Z, after deny_time_bound (hook.py:425) went live at 06:52:33Z; the rule matches only the word timeout. Acceptance: a counted sleep loop (a time bound by another name) is refused or replaced by a wait on the fact, and a run's step ends on its observed outcome.
