---
slug: harness-dep-follows-handed-fix
track: harness
title: a change whose limit's fix was handed to another change waits on the wrong
  one and never runs again
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T03:37:18Z'
---
sweep-30 P1-a: server-cache-clientscript-name-hash has been 'FAIL upstream at 8c6d9679e: dev' since 03:15:04Z with no run listed. Its limit (answer-7 on harness-carry-gh-pr-edit-classic-projects: upstream CI's openrs2 fetch) was deferred by carry run -5 to harness-deploy-survives-tools-ship (it reverted its gate.sh edit; 'nothing more was needed on the carry side'); carry went done 03:18:59Z; name-hash never depended on deploy-survives and its input does not change, so nothing re-runs it (no re-carry). A limit that moves to another change moves its dependency edge, and a FAIL upstream outside the head re-runs the upstream check once its cause is fixed. Also (sweep-30 P1-c): reply_only (hd.py:1303-1306) shows 'reply: qa run due' while a dev run is mid-fix (server-445, 03:27:22Z). evidence/monitor/sweep-30.md
