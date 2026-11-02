---
slug: harness-suite-failure-recorded
track: harness
title: a failed suite test leaves no record of its reason
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T03:37:19Z'
---
sweep-29 P1-a: EndToEnd.test_harness_change_defined_to_live failed once in harness-limit-of-holds-the-change-1's full run (03:11:52Z); its detail (the inner gate records, tests/test_hd.py:3227) went only to stderr, the run's grep dropped it, and SUITE_TMP removed the inner root, so the inner test cannot be named. A failed test's detail is written under the run's evidence or the gate rows. evidence/monitor/sweep-29.md

Also (filed): fork CI hangs in 'Generate cache and gameval sources' with no bound
sweep-30 P1-b: runs 41380418846 (gate/quest-runemysteries, since 02:57:18Z) and 41380970688 (gate/cannon-...gelgiq, since 03:03:38Z) were still in that step at 03:25Z; their hd.py rows processes 110585 and 217602 wait. a0ee32940 waits for openrs2 bytes before the step but nothing bounds a download that starts then stalls. A stalled step ends as the runner's fault and is re-run. evidence/monitor/sweep-30.md
