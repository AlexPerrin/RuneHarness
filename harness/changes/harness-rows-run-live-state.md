---
slug: harness-rows-run-live-state
track: harness
title: A change whose run is live says so, not 'dev run due'
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T18:25:40Z'
---
Sweep 67 P5: the state 'dev run due: head X not handed over' (hd.py:1625) is written while that change's run is alive (harness-live-http-mount 18:07:44Z and 18:18:08Z, run -1 live since 18:01:03Z; server-clan-channels 18:11:21Z, 11 s before its handover). Cosmetic: no duplicate listing. Evidence: evidence/monitor/sweep-67.md
