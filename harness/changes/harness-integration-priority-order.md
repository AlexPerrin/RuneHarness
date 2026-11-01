---
slug: harness-integration-priority-order
track: harness
title: A lower-priority change's conflict never blocks a higher-priority change's
  test-server deploy
kind: change
priority: P0
deps: []
created: '2026-11-01T11:23:24Z'
---
After server-friends-chat-clan-channels (P0) resolved its pin conflict, the test-server deploy of it and of cannon-review-354, genie-review-355 and goblin-diplomacy-review-367-fftgsrq (all P1, upstream in progress) is now 'blocked by quest-runemysteries's conflict' (P3, a new quest). The user's priority scheme (harness and blockers P0, upstream in progress P1, hunter-feat-pr P2, new quests P3) means a P3 head must not hold P0/P1 work. Expected: the integration tree merges gated heads in priority order (then creation date); a head that conflicts with higher-priority heads is left out of the tree (its own change gets the dev step to resolve), and the rest deploy. One test per requirement touched.
