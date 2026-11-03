---
slug: harness-mcp-restart-on-ship
track: harness
title: an mcp/ ship never reaches the running MCP servers
kind: change
priority: P1
mechanism: devtools
deps: []
created: '2026-11-02T03:14:22Z'
---
sweep-28 P1-a: harness-qa-login-idle shipped mcp/devtools_bridge.py's whole-call bound at 03:03Z, but the orchestrator's bridge (pid 2233412, child of claude --agent orchestrator, since 00:30Z) and another session's (pid 207818, 03:01Z) predate it, and all runs share the orchestrator's MCP, so a hung desktop call is still unbounded. A ship that changes mcp/ restarts (or tells the session to reload) the MCP servers it changed. evidence/monitor/sweep-28.md
