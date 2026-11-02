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

Also (filed): Every denial event names its change and run
Sweep 76 P5-a: denial events from a run's own agent carry agent/role but no change/run (hook.py:465, 484), e.g. state/events.jsonl:10942 and 11023 (agent ad4f77e7e1702ee54 = harness-live-stack-issuer-2 per state/runs/by-agent), while other denial paths name the run; grepping events by change misses them. Evidence: evidence/monitor/sweep-76.md
