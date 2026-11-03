---
slug: harness-suite-tmp-on-stop
track: harness
title: a stopped test suite leaves its temp root behind
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T01:33:24Z'
---
sweep-17 N6: /tmp/hd-suite-zk2pf16n (57M, mtime 01:08:43-01:09:34Z) belongs to the ship-harness gate stopped at 01:09:24Z (pid 2515598). tests/test_hd.py:12 SUITE_TMP = tempfile.TemporaryDirectory(...) and tools/server/test_tools.py:4 (tools-suite-) are removed only on a normal exit, so every stopped gate leaks one root. evidence/monitor/sweep-17.md
