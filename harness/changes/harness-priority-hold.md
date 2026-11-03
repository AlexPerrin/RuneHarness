---
slug: harness-priority-hold
track: harness
title: The user's word holds a priority band
kind: change
priority: P0
deps: []
created: '2026-11-01T12:10:43Z'
---
The user's word (2026-11-01, relayed to the orchestrator): "Do not action P3 work for now, Focus on the P0 and P1 queue". hd still lists spawns for P3 changes (quest-*, server-npc-examine-without-overlay), so only the orchestrator's restraint holds them. Expected: one recorded setting (the user's word, recorded by main) that keeps hd from spawning runs of changes whose effective priority is below the held band, until the user lifts it; a P3 change that blocks a P0/P1 change keeps its inherited priority and still runs. One test per requirement touched.
