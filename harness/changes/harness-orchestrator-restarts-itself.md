---
slug: harness-orchestrator-restarts-itself
track: harness
title: The orchestrator wraps up and restarts itself on its new definition, with no
  user step
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T00:06:52Z'
---
The user's word (2026-11-02): "Th orchestrator should warp up, and restart autonomously." Today, when the orchestrator's definition changes (harness-orchestrator-reloads-own-definition, d79c304), hd alerts it to write state/orchestrator-handoff.md, stop its monitor sweep and ask the user to run `claude --agent orchestrator`. Until the user does, the old session drives on: since ~23:55Z it has spawned more runs on the old definition, and the hand-off file goes stale with every spawn. Acceptance: (1) on the alert, the orchestrator writes the hand-off, spawns nothing more, and ends its own session once it holds nothing a fresh session can't rebuild from files; (2) a fresh orchestrator session on the new definition starts on its own: the user's terminal or a harness-owned supervisor relaunches it in ~/osrs-harness, and the user can still chat with it directly; (3) runs alive at the swap keep working, and their hand-backs reach the new session (or are recovered from run records, so no hand-back is lost); (4) the new session reads the hand-off, restarts the monitor sweep, and the alert clears; (5) a test drives a definition change through to a new session bound as the console, with no user step.
