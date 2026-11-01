---
slug: harness-subagents-stopped-at-handback
track: harness
title: A run's subagents are stopped when the run hands back
kind: change
priority: P1
deps: []
created: '2026-11-01T11:32:32Z'
---
The user's word (2026-11-01): keep subagents for lookups and tool use (good context management), just fix the stop bug. Observed: quest-ernestthechicken-2 and quest-childrenofthesun-3 each started a read-only subagent, then hit the context limit; TaskStop from the run was refused ('only the subagent can stop itself'), the answers were lost and the orchestrator stopped the orphans by hand. Expected: subagents stay allowed; when a run hands back (or its record is written), every subagent it started is stopped and its finished answer, if any, is kept in the run's evidence; a context-limit hand-off first collects or stops them. Fix the mechanism (hook on SubagentStop / the hand-back, or the role text plus a check), not the use. One test per requirement touched.
