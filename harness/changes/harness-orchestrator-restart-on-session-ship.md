---
slug: harness-orchestrator-restart-on-session-ship
track: harness
title: a ship of .claude/settings.json, .mcp.json or mcp/ entry points does not reach
  the running orchestrator
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T05:29:23Z'
---
sweep-42 P1-b: the orchestrator session (pid 2233291, since 00:19Z) runs devtools_bridge.py directly (pids 2233411/2233412), not through mcp/serve.py (1630cc9, 03:22Z), so no mcp/ change since then is live in the session that hosts every run (the whole-call bound, the no-port refusal); hooks also load only at session start, so the new PreToolUse matcher mcp__osrs-devtools-desktop__.* is not live. A ship that touches .claude/settings.json, .mcp.json or the mcp/ entry points raises one user: alert asking for the orchestrator restart (or the orchestrator restarts at a quiet point), naming what it would pick up. evidence/monitor/sweep-42.md
