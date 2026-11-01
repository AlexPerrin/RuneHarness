---
slug: server-examine-multi-transform
track: server
title: 'Examine: resolve multiloc and multinpc transforms for the player'
kind: change
priority: P2
deps:
- server-npc-examine-without-overlay
created: '2026-11-01T07:14:33Z'
---
On origin/main 31241beef, Examine on a multiloc or multinpc reads the base type's text: api/net/.../handlers/OpLoc6Handler.kt sends ServerCacheManager.getObject(message.id).desc and OpNpc6Handler.kt getNpc(message.id).examine, without the player's varp/varbit transform. Seen in game (quest-impcatcher-3, evidence/quest-impcatcher/table-before.txt, table-after.txt): Mizgog's table loc 16171 (multi on varp 160 -> 16169/16170) examines empty before and after Imp Catcher, while .data/raw-cache/examines/locs.csv holds 16169 'A table bearing a curious device.' and 16170 'A table bearing Mizgog's beads.'; Wizard Mizgog npc 5005 (multi -> 7746/7747, csv 'An old wizard.') examines empty. Fix: resolve the transform for the examining player with the existing multiLoc/multiNpc helpers (api/player/.../interact/LocInteractions, NpcInteractions) before reading desc/examine; together with server-npc-examine-without-overlay applying the csv to locs without an overlay (ObjectServerCodec.kt line 72 has the same 'if (customData != null)' pattern), so loc examines come from locs.csv. Verify in game: Mizgog's table before and after Imp Catcher and Mizgog give the wiki examines; a plain loc and npc still examine. Shared code: its own PR off main, merged before quest-impcatcher.
