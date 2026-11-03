---
slug: harness-server-quest-setting-per-change
track: harness
title: The server track's quest setting is per change
kind: change
priority: P1
deps: []
created: '2026-11-01T04:25:48Z'
---
The user's word, relayed from cannon-review-354-8 (PASS): under the server track's respect-progress setting no cannon can be set up, since main has no Dwarf Cannon quest registered. The QA ran its own server container outside track.sh with game.yml assume-completed to test, and its first restart broke the game.yml mount. Make the track's quest setting per change (a change's definition or contract picks respect-progress or assume-completed; up applies it to that run's server, restarts keep it), so QA never runs containers by hand. Also from that run: several cannon-review-354 accuracy rows passed on code reading plus earlier runs, not a run at that head (target-area shapes, damage roll, 1-in-4 destroy roll off KQ, 35 prohibited areas, ornamented locs, seq 827). Proof: a server up for cannon-review-354 with assume-completed sets up a cannon through track.sh alone, survives a restart, and those rows are judged at its head. One test per requirement touched.
