---
slug: harness-ps-test-unscoped
track: harness
title: The slice test passes outside a run's slice
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T21:16:07Z'
---
Sweep 85 P5-a: test_hd_ps_lists_the_slice_s_processes_but_its_own (tests/test_hd.py:2207) takes the slice from /proc/self/cgroup with split('/')[-2]; in an unscoped shell (0::/init.scope) that is '0::', so python3 -m unittest tests.test_hd.R5 run by the orchestrator or a monitor gives 1 false failure of 60. Evidence: evidence/monitor/sweep-85.md
