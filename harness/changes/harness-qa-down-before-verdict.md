---
slug: harness-qa-down-before-verdict
track: harness
title: A qa run's stack comes down before its verdict ends it
kind: change
priority: P1
mechanism: roles
deps:
- harness-reader-git-readonly
created: '2026-11-02T18:31:06Z'
---
Sweep 68 P4-a: qa.md:36 records hd verdict, then qa.md:52 says 'Before the hand-back run track.sh down'. The verdict ends the run at the next pass and processes-ended kills the in-flight down: hunter-feat-pr-25's down exited 144 and its retry was denied 'run ended: hand-off only' (state/events.jsonl 10655, 10663, 10665, 10668). dev.md:51 orders it right. Either qa runs down before hd verdict, or both roles drop the down since downs() covers it (docs/ARCHITECTURE.md:363). Evidence: evidence/monitor/sweep-68.md
