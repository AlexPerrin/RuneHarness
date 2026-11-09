---
slug: server-levelup-guide-messages
track: fork
priority: P2
upstream: false
---
LevelUpScript (api/stats-plugin) after a level-up sends 'Level N <Skill>: <unlock>' game messages and the levelup message type 118 '11|Check the <col=ef1020>skill guide</col> for more information about <Skill>.'. The Goblin Diplomacy RSProx recording (2026-10-16, rev 241, re/ref/rsprox/txt/20261016T082141-scrubbed.txt ticks 1802-1804, Crafting 1->3) shows only the level-up message, levelup_anim and jingle 36, then one type-118 message '11|Check the <col=ef1020>skill guide</col> to see what your new Crafting level unlocks!' and no per-unlock lines. Check other recorded level-ups and fix the guide prompt to match. Seen in game by goblin-367-rsprox-dump-16 (evidence/goblin-367-rsprox-dump/dev16/notes.md).

Carried from v8 at the cutover (2026-11-03): its head is dev/server-levelup-guide-messages on the fork; re-judged under v9's criteria.
