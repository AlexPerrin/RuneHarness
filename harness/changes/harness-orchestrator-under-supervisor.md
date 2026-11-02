---
slug: harness-orchestrator-under-supervisor
track: harness
title: hd restart refuses, and hd alerts the user, when the orchestrator does not
  run under tools/orchestrator.sh
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T15:28:02Z'
---
Sweep 60 P2-a: the live orchestrator pid 14859 is a bare 'claude --agent orchestrator drive' whose parent is a VS Code bash (pid 1554), with no tools/orchestrator.sh process; hd restart (cmd_restart) SIGTERMs the session and relies on the supervisor to start the next, so the first restart trigger (.mcp.json change, context past context_limit) ends the loop with no driver, and the 'no orchestrator session' alert has no session to show it. Check the session's parent is the supervisor; otherwise refuse the restart and raise a user alert to start it under tools/orchestrator.sh. Evidence: evidence/monitor/sweep-60.md
