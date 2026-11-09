---
slug: server-npc-examine-without-overlay
track: fork
priority: P2
---
On origin/main 31241beef, Examine on an NPC that has no TOML overlay (custom data) sends an empty NPC_EXAMINE message: or-cache/src/main/kotlin/dev/openrune/codec/osrs/impl/NpcServerCodec.kt sets examine = customData.examine ?: examines[obj.id] only inside 'if (customData != null)', so .data/raw-cache/examines/npcs.csv is never applied to such NPCs. Seen in game (quest-dorics-3, evidence/quest-dorics/doric-examine-wander.txt): Doric 3893 (csv: 'A dwarf smith. Quite handy with a hammer.') and Squirrel 1416 ('Bushy tail!') examine empty; Black bear 2839 (has an overlay) gives 'Eek! A bear!'. Fix: apply the csv examine for every NPC (overlay examine first, then csv); check ObjectServerCodec's loc desc for the same pattern. Verify in game: Doric, a squirrel and a black bear give their wiki examine. Shared code: its own PR off main, merged before quest-dorics.

Carried from v8 at the cutover (2026-11-03): its head is dev/server-npc-examine-without-overlay on the fork; re-judged under v9's criteria.
