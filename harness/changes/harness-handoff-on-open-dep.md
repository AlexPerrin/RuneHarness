---
slug: harness-handoff-on-open-dep
track: harness
title: A hand-off whose only leftover is an open dependency makes no run due until
  that dependency moves
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T21:56:47Z'
---
Sweep 89 round 2 P2-a: client-login-segv-osclient-6 handed off at 21:49:55 (ended record:false, state/events.jsonl:11638); its handoff.md says the SIGSEGV is gone, up-run6 failed at LoginIndex 3 (already carried by harness-live-stack-issuer), nothing new filed, and it was dispatched while that dep was open. 3 s later hd listed client-login-segv-osclient-7 (11639, 'dev run due') because the new handoff.md mtime is run input (hd.py:~1723 input=[..., hoff mtime]); it would list run 8 after every hand-off until the issuer lands. The legacy joined row answer-5 had no holds: field (the orchestrator added it by hand). A hand-off naming only an open dependency should not make a run due until that dependency moves. Evidence: evidence/monitor/sweep-89.md
