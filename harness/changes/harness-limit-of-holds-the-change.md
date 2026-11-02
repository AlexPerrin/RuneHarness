---
slug: harness-limit-of-holds-the-change
track: harness
title: a --limit-of filing joined into an open change does not hold the change it
  limits
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T03:08:28Z'
---
goblin-367-rsprox-dump-7, cannon-354-...gelgiq-5, server-friends-chat-clan-channels-21 each filed the openrs2 freshCache fault with hd new --limit-of <self>; it joined harness-deploy-survives-tools-ship, but none of the three gained it as a dependency, so each was 'gate failed: dev' again at the same head and goblin-367-rsprox-dump-8 was listed for nothing (03:1xZ). A limit-of filing, new or joined, adds the change it carries to the limited change's deps (as --blocks does). The orchestrator added the dep by hand to goblin, cannon, friends-chat, genie-review-355 and server-token-auth.
