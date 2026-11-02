---
slug: harness-supervised-resolves-path
track: harness
title: A session under tools/orchestrator.sh started as ./orchestrator.sh counts as
  supervised
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T18:08:35Z'
---
hd alerts 'user: no orchestrator session under tools/orchestrator.sh: /exit orchestrator 2137180' although pid 2137180 (claude --agent orchestrator drive) has parent 2137176 '/bin/bash ./orchestrator.sh', started from ~/osrs-harness/tools. supervised() (hd.py:505-508) tests that a cmdline arg endswith 'tools/orchestrator.sh'; the user ran it as ./orchestrator.sh, so the arg is './orchestrator.sh' and the test fails. hd restart would also refuse (hd.py:2710). Resolve the arg against the parent's cwd (/proc/<ppid>/cwd) and compare to ROOT/SUPERVISOR. Evidence: ps -o pid,ppid,args -p 2137180 2137176 (2026-11-02 ~18:10Z)
