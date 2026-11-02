---
slug: harness-gate-ci-cache-miss-cannon
track: harness
title: A gate CI run cancelled in the game cache download is recorded as the head's
  FAIL
kind: change
priority: P1
mechanism: build-gate
limit-of:
- cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq
deps: []
created: '2026-11-02T01:10:50Z'
---
cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq's gate failed at a correct head (86f1fd48d, T 7a487d9a2, gate sha 9389a59cc): CI run 41366859771 on its gate branch missed actions/cache game-cache-v2-03bcedaa... ('Cache not found'), spent 00:23:18Z-00:52:06Z in 'Generate cache and gameval sources' (openrs2 download) and was cancelled by ci.yml's timeout-minutes 30 in 'Compile and run tests' before any test task; Formatting passed. The head's own tests pass (evidence test.log: NulodionLostCannonTest 7 tests, 0 failures). Same root cause as gate-ci-cache-scope and planner-19 on this mechanism: the gate branch cannot restore the cache saved on other gate refs, and a cancel outside the head is recorded as the head's FAIL and sends a dev run that can change nothing. Acceptance: as harness-build-gate-keyed-process; this change re-gates the same head once the cause is gone.

Also (filed): local builds re-download the 213 MB openrs2 cache; one tree is built twice under two keys
sweep-15 B3: live deploy track.sh ship integration 1c0d3aa41 (tree f88b47fb3, from 00:46:27Z) sat in :or-cache:freshCache at ~120 KB/s (state/integration/build-f88b47fb3*.log); 12 more fresh downloads today (live 19:03Z/22:35Z, integration 23:13Z, hunter-feat-pr, server-clan-channels x3, goblin-367 22:19Z). gate.sh:63-67 /dl reuse fills only after a cache-step miss and its */*/*-disk.zip glob seems never to match; store key s-$CK moves with every pack change. Local builds and deploys must reuse one cache copy (the game-data release asset). sweep-15 B4: server-token-auth tree 2cdbf708b built as -c0485930ffdf3 (dev, 00:44:39Z) and -c0485930ffdf3-d5b822a10a10 (pass, 00:47:01Z): the dev run's build key leaves out CENTRAL. evidence/monitor/sweep-15.md
