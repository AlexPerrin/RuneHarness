---
slug: quest-miniquest_daddyshome
track: server
title: 'Daddy''s Home (miniquest): 1:1 with the official game'
kind: change
priority: P4
goal: server-content
units:
- quest:miniquest_daddyshome
created: '2026-11-01T00:54:30Z'
deps: [harness-no-powershell, harness-server-build-musicrepository, harness-desktop-first-login]
---
Unit quest:miniquest_daddyshome of goal server-content (harness/goals/server-content.json) measures 0: no change names it. The quest is on upstream main (OpenRune/OpenRune-Server origin/main 31241beef, content/quest/src/main/kotlin/org/rsmod/content/quest/area/varrock/daddyshome) but unverified against the official game. Play it through start to finish on the test server and compare each step (start requirements, dialogue, items, varps/varbits, journal, scenery and NPC interactions, cutscenes, rewards and quest points) with RSProx recordings and the wiki; fix every divergence in this change. The passing verdict on the live change marks quest:miniquest_daddyshome.
