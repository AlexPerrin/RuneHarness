---
slug: harness-hold-counts-only-listable
track: harness
title: The tier hold counts only a higher run the pass can list
kind: change
priority: P0
deps: []
created: '2026-11-01T18:36:28Z'
---
Observed 2026-11-01 18:35Z by the orchestrator: client-down-stops-mobile-login [client P1] has shown 'dev run due' since 04:17Z and has never been listed (no run since client-down-stops-mobile-login-1 ended at 04:13Z), yet under the hold-on-due rule it holds every P2-P4 change: genie-review-355's dev run (owner of the content/looting-bag pin conflict) is 'listed' as genie-review-355-99 in events.jsonl and then never appears as a spawn; cannon-354-reset-mcannonmulti (dev due) and cannon-354-return-after-destroy (review due) do not spawn either. A change that holds others but is itself never listed starves the queue. Acceptance: the hold counts a higher change only if this pass lists its run (or its run is alive); a due run that the pass cannot list (why ever) holds nothing and is surfaced as an alert naming the reason; a test covers a due-but-unlistable P1 beside a due P2: the P2 is listed and the alert shows.
