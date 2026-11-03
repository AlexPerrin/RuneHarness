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

Also (filed): a verdict and its card name no run
sweep-21: cmd_verdict records run = os.environ HD_RUN (hd.py:2625), which nothing sets, so cards print 'verdict at ...: 22 rows pass (run )' (hd.py:2345; 02:05:46Z) and most verdicts.jsonl rows have run ''. Take the run from the change's started, unended qa run record. evidence/monitor/sweep-21.md
