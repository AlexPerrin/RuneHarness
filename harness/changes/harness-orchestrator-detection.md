---
slug: harness-orchestrator-detection
track: harness
title: hd sees the orchestrator session that is running
kind: change
priority: P0
deps: []
created: '2026-11-01T12:17:18Z'
---
The user (2026-11-01, relayed by main, message 8): the orchestrator is running for sure, yet hd keeps 'user: no orchestrator session'. Evidence: hd.py F.orchestrator() (R2) looks for a process whose argv is claude ... --agent orchestrator; on this machine both live claude processes (pids 2062, 1827063) show /proc/<pid>/cmdline as just 'claude' with no arguments, so the orchestrator is never found. Expected: hd detects the live orchestrator session from a fact the session itself leaves (for example a mark it writes when it runs hd or arms its watch, checked against its live pid), not from argv; the alert shows only when no orchestrator session is alive. One test per requirement touched.
