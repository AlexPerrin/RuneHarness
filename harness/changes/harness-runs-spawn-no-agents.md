---
slug: harness-runs-spawn-no-agents
track: harness
title: Runs do their own lookups; no run spawns a subagent
kind: change
priority: P1
deps: []
created: '2026-11-01T11:19:50Z'
---
Twice a run started a read-only subagent, hit its context limit, and could not stop it ('only the subagent can stop itself'): quest-ernestthechicken-2 (Draynor basement facts) and quest-childrenofthesun-3 (1637 cutscene timings). The answers were lost, the next run had to redo the lookup, and the orchestrator stopped the orphans by hand. Expected: the dev and qa role files say a run does its lookups itself (reading recordings, wiki, cache through its own tools) and starts no agent; if the platform lets the role's tool list drop the Agent tool, it does. One test per requirement touched.
