---
slug: quest-cooksassistant
track: server
title: 'Cook''s Assistant: 1:1 with the official game'
kind: change
priority: P3
goal: server-content
units:
- quest:cooksassistant
created: '2026-11-01T00:54:29Z'
deps: [harness-no-powershell, harness-server-build-musicrepository, harness-desktop-first-login]
finding: [IC_kwDOQBbPT88AAAABh3zv1Q]
---
Unit quest:cooksassistant of goal server-content (harness/goals/server-content.json) measures 0: no change names it. The quest is on upstream main (OpenRune/OpenRune-Server origin/main 31241beef, content/quest/src/main/kotlin/org/rsmod/content/quest/area/lumbridge/CooksAssistant.kt) but unverified against the official game. Play it through start to finish on the test server and compare each step (start requirements, dialogue, items, varps/varbits, journal, scenery and NPC interactions, cutscenes, rewards and quest points) with RSProx recordings and the wiki; fix every divergence in this change. The passing verdict on the live change marks quest:cooksassistant.

Also: #445's review round: eaglepurerocketgrape's finding IC_kwDOQBbPT88AAAABh3zv1Q (the interrupted ending), which server-445-cickwdoqbbpt88aaaabh3zv1q carried and this change supersedes: fix it with a commit on the head and answer it in pr-reply-IC_kwDOQBbPT88AAAABh3zv1Q.md quoting it.
