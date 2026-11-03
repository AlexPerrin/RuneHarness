---
slug: harness-running-holds-nothing
track: harness
title: A running higher run holds no lower work; only a higher run due and not yet
  started does
kind: change
priority: P0
deps: []
created: '2026-11-01T19:21:50Z'
---
The user's word (2026-11-01): "don't let running higher runs hold lower work. Just hold off on P3 work, and ill close unecessary P2s". Today (hold-on-due-only, hold-counts-only-listable) a higher change whose run is alive holds every lower tier: while harness-public-queue-on-fork-1 (P0) runs, cannon-354-reset-mcannonmulti's QA review (P2) is due and not listed though agent slots are free. The 'hold off on P3' part is hd.yaml hold: P2 (set by the orchestrator). Acceptance: the tier hold counts only a higher change whose run is due this pass and not yet alive (a listed or alive run holds nothing); the hd.yaml hold band still applies; the R6 test covers a P0 run alive beside a due P2: the P2 is listed.
