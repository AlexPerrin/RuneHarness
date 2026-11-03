---
slug: server-content
track: fork
target: 100
measure: query
---
## Goal
100% of the content inventory 1:1 with the official game. The inventory is `harness/goals/server-content.json`: one
row per content unit from the cache ({unit, source}). A unit passes only by a passing verdict on a change that names
it (`units:` of harness/changes/<slug>.md, `goal: server-content`) and is landed on staging, the tree the test server
runs; the pass computes the share whenever staging's tree moves (a `measure` row per tree). An empty inventory
measures 0: the first change the planning run files is the inventory itself.

## Unit kinds
A content unit is one row of a cache dbtable below; its unit is `<kind>:<row name minus the prefix>` and its source
`dbrow.<name>=<id> dbtable.<table>=<id>`, from the dbrows and gameval names osrs-mcp serves. A new cache revision
regenerates it as a change on this goal.

| kind | dbtable | row prefix |
|---|---|---|
| quest | quest (quests, miniquests, Recipe for Disaster subquests) | quest_ |
| skill | hiscores_skill_info | hiscores_skill_ |
| minigame | minigame_teleport | minigame_ |
| boss | hiscores_bosses_info | hiscores_bosses_ |
