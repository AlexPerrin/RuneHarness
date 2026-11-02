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

Also (filed): One monitor sweep runs until its context fills, reporting as it goes
The user (2026-11-02 ~21:50Z): 'Monitor sweep lifecycles too quick, allready on iteration 89, can keep running until its context starts to fill.' orchestrator.md step 11 starts a fresh read-only sweep after each report (sweeps 66-89 today, one every ~5-15 min). Change it so one sweep keeps sweeping in rounds, sends each round's findings to the orchestrator as it goes (filed by root cause as now, evidence/monitor/sweep-<n>.md appended per round), and ends only when its context nears the limit, then the next starts.
