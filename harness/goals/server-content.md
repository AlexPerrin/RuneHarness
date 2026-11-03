---
slug: server-content
track: server
target: 100
---
## Goal
100% of the content inventory 1:1 with the official game. The inventory is `harness/goals/server-content.json`: one
row per content unit from the cache ({unit, source}). A row passes only by a passing verdict on a live change that
names its unit (`units:` of harness/changes/<slug>.md, `goal: server-content`); hd hands the passing units to the
track's `measure` verb as PASSES, which prints the share of rows passing and writes the report. An empty inventory
measures 0: the first change the orchestrator files is the inventory itself.

## Unit kinds
A content unit is one row of a cache dbtable below; its unit is `<kind>:<row name minus the prefix>` and its source
`dbrow.<name>=<id> dbtable.<table>=<id>`. `harness/goals/server-content.py` regenerates the inventory from the files
osrs-mcp serves (the LIVE cache's dbrows, gamevals.dat's names).

| kind | dbtable | row prefix |
|---|---|---|
| quest | quest (quests, miniquests, Recipe for Disaster subquests) | quest_ |
| skill | hiscores_skill_info | hiscores_skill_ |
| minigame | minigame_teleport | minigame_ |
| boss | hiscores_bosses_info | hiscores_bosses_ |
