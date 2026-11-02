---
slug: harness-gate-held-row-own-stop
track: harness
title: A gate row is held only for a stop of its own process, not any run's stop
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T14:55:36Z'
---
Sweep 57 P3-a: stopped() writes one global time to state/stopped on every slice and script stop (hd.py:307, hd.py:350); hd.py:2976 holds any signal-ended gate row if any stop happened while it ran, whatever run it belonged to, so a head's JVM crash (exit >128) during another run's end records no verdict and re-runs, against e9d4d02 ('any other end, a crash among them, is the head's'). Repeated processes-ended events widen the window: quest-completion-recorded-ticks-2 ended at 14:51:00Z and 14:51:23Z; server-world-entities-9 six times 03:34-03:40Z (state/events.jsonl:8314-8352), from the cleanup loop hd.py:2532-2536. Fix at the root: tie the stop to the row's own process or slice. Evidence: evidence/monitor/sweep-57.md
