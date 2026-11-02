---
slug: server-world-entity-login-tick
track: server
title: A world entity is added at login on the official tick without blanking the
  scene
kind: local
priority: P2
deps:
- server-world-entities
created: '2026-11-02T20:04:30Z'
---
From qa run server-world-entities-16 (PASS at bfb9d9853, 2026-11-02 ~20:05Z): the head adds the raft world entity at login only after the client's MAP_BUILD_COMPLETE, while RSProx 944 shows the official server adding it on tick 1, before MAP_BUILD_COMPLETE (tick 3), without blanking the scene. accuracy.md records this as an unsourced reconstruction; per the accuracy rule a divergence is fixed, not recorded. The qa noted the real cause of the earlier blanked logins (2 of 5 fresh-client dock logins on the previous head) may be in how this server rebuilds the map. Find that cause and add the entity on the recorded tick. Evidence: evidence/server-world-entities/qa16-dock-rounds.txt, evidence/server-world-entities/in-game.md, RSProx 944
