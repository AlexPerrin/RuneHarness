---
slug: harness-hold-p3-while-higher-open
track: harness
title: Spawn no P3 run while a P0-P2 change is open
kind: change
priority: P2
deps: []
created: '2026-11-01T12:42:58Z'
---
The user's word: "No quests are p3, focus on higher priority work". The loop spawned P3 quest runs (quest-childrenofthesun, quest-ernestthechicken, quest-sheepshearer, quest-runemysteries) into free slots while P0-P2 changes were open but waiting on dependencies; the user stopped them by hand three times. Acceptance: hd lists no spawn for a P3 change while any P0-P2 change is open (not closed), waiting or not; a test covers both cases.
