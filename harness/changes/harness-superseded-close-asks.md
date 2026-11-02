---
slug: harness-superseded-close-asks
track: harness
title: nothing tells the user a superseded change waits for their close
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T04:00:28Z'
---
sweep-32 P2-b: 11+ superseded changes wait for the user's hd close, and nxt (hd.py:1452) gives a silent wait: no alert or card says so, so the orchestrator lists them by hand. A superseded change raises one user: alert naming its close command. evidence/monitor/sweep-32.md
