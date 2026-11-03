---
slug: harness-restart-alert-names-stale
track: harness
title: the restart alert names hooks as stale though they reached the session
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T05:56:32Z'
---
sweep-44 P2-c: the 05:39:13Z alert says the session lacks .claude/settings.json changes, but the running session does run the new desktop PreToolUse hook (it denied world-entities-10's portless call at 05:29:35Z); what the session lacks is .mcp.json (serve.py and the new bridge). The alert names only what is stale (alert on .mcp.json alone). evidence/monitor/sweep-44.md
