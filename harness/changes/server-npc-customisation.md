---
slug: server-npc-customisation
track: fork
priority: P2
goal: client-api
---
# NPC body/head customisation is never sent, so the client holds no NpcOverrides

Blocks the client-api probe's NpcOverrides rows (getModelIds, getColorToReplaceWith, getTextureToReplaceWith, useLocalPlayer: 4, unreached in evidence/client-api/api-probe.tsv at 90.3%). The Android host already reads NPC overrides (client-state.md 'Cache, index and config'); they stay null because OpenRune sends no NPC body/head customisation extended info (rsprot's NPC info BodyCustomisation/HeadCustomisation).

Repro: log in the tester anywhere; for every NPC in list_npcs, NPC.getModelOverrides()/getChatheadOverrides() is null. Expected (official): the NPCs whose official server sends body or head customisation (find one from RSProx recordings and the wiki, accuracy skill) carry it in NPC info; minimum to unblock the client: one such NPC, as the official server sends it, in a scene the tester reaches.
