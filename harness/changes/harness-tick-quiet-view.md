---
slug: harness-tick-quiet-view
track: harness
title: The tick's journal does not reprint an unchanged card every pass
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T21:31:23Z'
---
Sweep 87 P5-a: cmd_tick (hd.py:3701+) prints the whole view each pass, so the goblin-367 card is reprinted every minute while it waits for the user: hd-tick.service wrote 830 KB of journal 21:00-21:29Z (~40 MB/day). Print only what changed since the last pass (the wake already carries head lines). Evidence: evidence/monitor/sweep-87.md
