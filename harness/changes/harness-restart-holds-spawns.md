---
slug: harness-restart-holds-spawns
track: harness
title: an orchestrator restart freezes every spawn until the old session collects
  its runs, and stops a mid-review qa run
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T00:57:41Z'
---
sweep-14 B2: definition shipped 00:15:16Z; no spawn until 00:43:00Z though slots were free from ~00:19Z; six listed runs waited up to 23 min (server-friends-chat-clan-channels-20 listed 00:19:51Z); genie-review-355-131 'stopped by the head' 00:41:47Z mid-review, -132 restarts from scratch. A wrap-up must not block listed runs (or the new session takes them over), and a live run goes on across the swap. evidence/monitor/sweep-14.md
