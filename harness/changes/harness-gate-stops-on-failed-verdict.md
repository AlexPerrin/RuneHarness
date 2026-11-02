---
slug: harness-gate-stops-on-failed-verdict
track: harness
title: a gate keeps running on a head whose verdict already failed
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T04:13:17Z'
---
sweep-33 P2-c: server-world-entities' gate (started 03:54:34Z, state/server-world-entities/proc-gate.json) still ran at 04:12Z after the 03:58:15Z FAIL verdict; since 7e97cd0 that head is the dev's, so the result changes nothing. Stop a gate when a FAIL verdict lands on its head. evidence/monitor/sweep-33.md
