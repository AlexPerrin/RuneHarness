---
slug: harness-run-stop-ends-processes
track: harness
title: Ending a run ends its processes
kind: change
priority: P0
mechanism: runs
deps: []
created: '2026-11-01T22:59:21Z'
---
Monitor sweep 7 (2026-11-01 22:57Z): harness-spotless-row-complete-1 was ended by hd stop at 22:48:06Z, but its test tree (root pid 3325061, track.sh gate e2e, cwd its worktree, /tmp/tmp6h3eg_sn) kept running, was reparented to init and recursed 25 levels (119 -> 253 processes); the orchestrator killed 259 processes at 22:58Z. hd stop (cmd_stop) writes only ended/reason; nothing stops a run's processes. Root cause against PRD R5 ('only stop processes you started'): a run is not one unit (agent + the processes it started) that ends together. Acceptance: every process a run starts (its bash tool calls, track.sh, tests) runs in a per-run systemd scope (or process group recorded at bind); hd stop, a run's end, its context-limit handoff and the pass dropping it all stop that scope; a test ends a run with a live child process and checks the child is gone.

Also (filed): A run, a gate and a test leave no temp directories behind
Monitor sweep 10 (2026-11-01 23:23Z): 4,448 /tmp/tmp* dirs (1.8 GB), 427 created since 23:00Z; test_hd.py:12's HD_ROOT mkdtemp is never removed and its rmtree calls sit at the end of tests (2095-2438), so a failure skips them; 288 tmp.*/index dirs match gate.sh:108 'mktemp -d' whose trap does not clean up. Also from the same sweep: a nested agent that is idle outlives its run, because stop_orphan acts only on its next tool call. Acceptance: tests use addCleanup/TemporaryDirectory (removed on failure too) and HD_ROOT is removed at suite end; gate.sh's temp index is removed on every exit path; a run's nested agents end with the run (its slice), not at their next tool call; a test checks no temp dir survives a failing test and a gate.
