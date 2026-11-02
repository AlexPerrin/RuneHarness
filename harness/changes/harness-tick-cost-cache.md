---
slug: harness-tick-cost-cache
track: harness
title: 'A pass rereads only facts that changed: tick cost stays within its timer'
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T21:51:08Z'
---
Sweep 89 round 1 P2-b: hd-tick CPU 15.2s at 21:36 then 19.5, 15.4, 22.0, 24.9, 41.4, 17.4, 44.4, 21.8, 43.9, 24.4 through 21:48 (was ~10s); some passes take 70-74s wall against the 60s timer, so ticks run back to back. In the 21:48 pass hd.py had 4.5s itself and 19.6s in children (13s system, process spawns); a 50 ms sample counted 116 gh api and 91 git merge-base --is-ancestor (71 in the harness repo, one per harness change; 331 of 416 definitions are harness), plus central fetch and set-head. Each pass rereads per-change git and gh facts with subprocesses and keeps no cache across passes; cost grows with open gates and definitions. Cache facts across passes keyed on the refs they read; skip done changes. Evidence: evidence/monitor/sweep-89.md
