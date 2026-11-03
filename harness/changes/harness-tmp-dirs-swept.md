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

Also (filed): a run killed after its hand-back stays alive in the record and holds a slot
sweep-15 B2: harness-build-gate-keyed-process-2 ended 00:56:01Z; the orchestrator's SendMessage resumed it 00:56:03Z (SubagentStart -> hook.py:135 fact resumed -> hd.py:698 ended=None); TaskStop killed it 00:56:08Z, no end fact followed; ended stayed null until hd stop 01:01:32Z: 5.5 min holding a slot (hd.py:1772 busy), blocking its change's next dev run (hd.py:1037 alive_run). The end of a run is a fact only SubagentStop writes; a kill must end it too. evidence/monitor/sweep-15.md
