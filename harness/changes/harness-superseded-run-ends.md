---
slug: harness-superseded-run-ends
track: harness
title: a superseded change's started run is not ended by the pass
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T02:01:00Z'
---
sweep-20: hd.py:2202 ends a started run only when its change is closed or done, while ARCHITECTURE.md:70 and hd.py:1341 say a superseded change holds with no runs. harness-run-idle-logout-off was superseded at 01:54:03Z; run -2 (started 01:53:42Z) stayed live until the orchestrator's TaskStop at 01:56:12Z (state/runs/harness-run-idle-logout-off-2.json). Treat superseded like closed there. evidence/monitor/sweep-20.md
