---
slug: harness-orchestrator-self-restart
track: harness
title: The orchestrator cannot restart itself for a long run
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T07:59:23Z'
---
The user (2026-11-02 ~08:05Z): "I'll start orchestrator script manually on my end. Consider how to restart the orchestrator autonomously in the future for long running." Today the orchestrator ran 13 h on one session: its MCP bridges predated mcp/serve.py and never reloaded (401s for every run's desktop calls, the owner guard held open), and only a manual restart cleared it. tools/orchestrator.sh `exec`s claude once, so ending the session leaves the user at a shell; hd has no restart verb; the live definition no longer reads a hand-off file at start, so a restart's context rides only on memory. Acceptance: the supervisor relaunches the session whenever it ends (a loop in tools/orchestrator.sh that stops only on the user's word), and the session restarts itself on an observed fact (a stale .mcp.json/bridge or definition, or the context nearing its limit): it spawns nothing new, lets live runs hand back, writes state/orchestrator-handoff.md, ends itself; the next session reads and deletes that file at start. No restart ever loses a hand-back or an open question to the user.

Also (filed): The orchestrator supervisor stops on the user's exit and does not relaunch a claude that fails at start
harness-orchestrator-self-restart-1 (bdf4925) left as unchecked risks, its own limits: (1) a user's exit while state/orchestrator-handoff.md exists still starts another session; (2) a claude that fails at once with a non-zero exit is relaunched endlessly; (3) unverified that Claude Code exits on SIGTERM and that /exit or double Ctrl-C exit 0. Evidence: evidence/harness-orchestrator-self-restart/
