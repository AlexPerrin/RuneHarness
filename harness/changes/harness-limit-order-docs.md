---
slug: harness-limit-order-docs
track: harness
title: The context-limit hand-off order reads the same everywhere
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T19:45:30Z'
---
Sweep 75 P5-a: e3fe9dd/b1f1686 reordered the context-limit hand-off to stop processes before recording what was judged (qa.md:44, hook.py:633-640, docs/ARCHITECTURE.md:447), but hook.py:28 (header table) and docs/PRD.md:270 still say 'record what it judged, collect its subagents and stop its processes'. Quick doc fix. Evidence: evidence/monitor/sweep-75.md
