---
slug: server-content
track: server
target: 100
---
## Goal
100% of the content inventory 1:1 with the official game. The inventory is `harness/goals/server-content.json`: one
row per content unit from the cache ({unit, source, passes}); a row passes only by a verdict of a change that names
the unit. The track's `measure` verb prints the share of rows passing and writes the report. An empty inventory
measures 0: the first change the orchestrator files is the inventory itself.
