---
slug: server-content-inventory
track: harness
mechanism: goals
title: 'Server-content inventory: one row per content unit from the cache'
kind: change
priority: P1
goal: server-content
deps: []
created: '2026-11-01T00:36:10Z'
---
The goal server-content measures 0 on an empty inventory (state/server-content/measure.json: {"tree": "9a551147eaeb...", "value": 0.0, "report": ".../harness/goals/server-content.json"}; harness/goals/server-content.json is []). harness/goals/server-content.md: "the first change the orchestrator files is the inventory itself".

Fill harness/goals/server-content.json with one row per content unit {unit, source, passes: false}, generated from the cache (osrs-mcp cache_search / gameval_search) by a committed script so it can be regenerated: unit = a stable name (e.g. quest:cooks_assistant, minigame:..., skill:<skill>:<method>), source = the cache reference (gameval name/id, enum or param) it came from. Define the unit kinds once in harness/goals/server-content.md (which cache tables count as content), so the orchestrator can file one server change per unit or group. No row passes yet. One test per requirement touched (R1); prove with one real `tools/track.sh measure server-content` printing 0 over a non-empty inventory.
