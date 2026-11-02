---
slug: harness-tmp-dirs-swept
track: harness
title: temp dirs left by pre-fix branches are never removed
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T00:57:42Z'
---
sweep-14 B8: 5081 /tmp/tmp* dirs (1.9G), 17:00-23:58Z, from branches cut before harness-run-stop-ends-processes; none new since 23:58:24Z, nothing sweeps the old ones. evidence/monitor/sweep-14.md
