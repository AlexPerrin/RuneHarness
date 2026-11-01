---
slug: harness-live-deploy-evidence
track: harness
mechanism: server
title: Each test-server deploy attempt keeps its own log, and a retry reuses the cache
kind: change
priority: P1
deps: [harness-tools-pinned-per-process]
created: '2026-11-01T22:35:36Z'
---
Monitor sweep 5: the ship of integration ee13b4cf (live b5e0bddbc) failed on attempt 1 between 22:08:13 and 22:09:21Z; attempt 2 writes the same file state/live/build-b5e0bddbc...-c0485930ffdf3.log, so attempt 1's failure is gone; attempt 2 re-downloads the 213 MB cache (or-cache:freshCache, ~16 min) where live builds took 31-52 s; state/live/ship.log has 13 first-attempt 'build failed' lines today; the test server has been at 7e4f3525c since 19:20Z. Root cause: deploy evidence is keyed by tree, not by attempt, and the cache is tied to the build tree. Acceptance: each attempt writes build-<tree>-<attempt>.log and its failure line is in ship.log; the cache volume is shared across build trees (keyed by cache version); the cause of the first-attempt failures is found and fixed; a test covers two attempts keeping two logs.

Orchestrator (2026-11-01 23:30Z): harness-tools-pinned-per-process carries a rebased copy of this change's tools commit 40c5cd5 and rewrites it; this change ships after it, and its next rebase drops the duplicate.
