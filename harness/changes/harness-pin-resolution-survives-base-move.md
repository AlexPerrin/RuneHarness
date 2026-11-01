---
slug: harness-pin-resolution-survives-base-move
track: harness
title: A pin's recorded resolution keeps serving after the base moves past its partner
kind: change
priority: P0
deps: []
created: '2026-11-01T15:27:44Z'
---
Every pin resolution goes stale when upstream main gains any commit, so the integration tree holds and every server change's test server deploy blocks until a dev re-resolves all of them.

Evidence:
- hd alerts (planner-10 brief): 8 pins conflict at once: content/looting-bag, content/pirates-treasure, fix/22-music-tab-play, fix/25-ice-mountain-music-area, fix/71-item-config-tradeable, local/android, local/test-commands, local/treasure-trails.
- events.jsonl 2026-11-01T15:25:08Z: server-token-auth 'test server deploy blocked by fix/22-music-tab-play's conflict'.
- origin/main moved 31241beef -> db69cb0c1 (github-actions[bot] 'chore: refresh content progress report', 14:51Z, touches only PROGRESS.md, README.md, tools/progress/wiki-cache.json).
- The fork holds local/merge/{8b3cfac,7f22b20,ededdf3,ca5b0d3,70e0267,6ca12a5}-31241be: bound to the old base sha, so integration() no longer finds them (it looks up local/merge/<h7>-<partner7> with the exact current partner).
- git merge-tree origin/main 8b3cfaca4 (fix/22) conflicts in MusicTabScript.kt; git merge-tree origin/main ab2cdb17d (its resolution local/merge/8b3cfac-31241be) is clean. The resolution still applies; only the lookup fails.
- The live tree (state/live/tree.json, 9638f309c) carried all of these pins with those resolutions.

Done when: integration() uses a recorded resolution of a pin head with a partner that is an ancestor of (or equal to) the current partner, so a base move that does not touch the conflicting files keeps the tree; only a resolution that itself no longer merges leads to the existing dev step or alert. With the fork as it is now, hd tick --dry-run shows no pin conflict from the 31241be resolutions and server-token-auth reaches its test server deploy. One test per requirement touched.
