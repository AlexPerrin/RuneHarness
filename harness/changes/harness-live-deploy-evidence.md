---
slug: harness-live-deploy-evidence
track: harness
mechanism: server
title: Each test-server deploy attempt keeps its own log, and a retry reuses the cache
kind: change
priority: P1
deps:
- harness-build-gate-keyed-process
created: '2026-11-01T22:35:36Z'
superseded: harness-server-stack-deploy
closed: 'answer-3: superseded by harness-server-stack-deploy'
---
Monitor sweep 5: the ship of integration ee13b4cf (live b5e0bddbc) failed on attempt 1 between 22:08:13 and 22:09:21Z; attempt 2 writes the same file state/live/build-b5e0bddbc...-c0485930ffdf3.log, so attempt 1's failure is gone; attempt 2 re-downloads the 213 MB cache (or-cache:freshCache, ~16 min) where live builds took 31-52 s; state/live/ship.log has 13 first-attempt 'build failed' lines today; the test server has been at 7e4f3525c since 19:20Z. Root cause: deploy evidence is keyed by tree, not by attempt, and the cache is tied to the build tree. Acceptance: each attempt writes build-<tree>-<attempt>.log and its failure line is in ship.log; the cache volume is shared across build trees (keyed by cache version); the cause of the first-attempt failures is found and fixed; a test covers two attempts keeping two logs.

Orchestrator (2026-11-01 23:30Z): harness-tools-pinned-per-process carries a rebased copy of this change's tools commit 40c5cd5 and rewrites it; this change ships after it, and its next rebase drops the duplicate.

Also (filed): A run's own server never idle-logs out the run's clients while the run is alive
The user saw 2/3 clients show 'You were disconnected from the server.' A lookup found genie-review-355-131's two desktops (instances 3 and 4) logged out at 00:19:59Z and ~00:21:01Z, about 5 minutes after the agent's last input (00:15:39Z). The server was up throughout, with no crash and no restart. The run's game.yml has idleLogout=true. An agent that spends more than 5 minutes thinking or reading loses its login, and its next in-game check fails or needs a re-login. Acceptance: a run's own server (track.sh up for a run) starts with idleLogout off, or the devtools keep the run's clients active; the live test server keeps the official idle logout; a test checks the run's rendered game.yml.

Also (filed): server track.md calls the desktop token login auth type 7; rsprot decodes token login as auth type 2
server-token-auth-13 hand-back: ~/src/OpenRune-Server/.worktrees/harness/tools/track.md:64 says 'login (auth type 7)'. rsprot 241 GameLoginDecoder decodes token login as auth type 2 (server-token-auth-12 QA FAIL on the same fact in game.example.yml, fixed at e40d5e9dd). Fix the harness doc to auth type 2.
