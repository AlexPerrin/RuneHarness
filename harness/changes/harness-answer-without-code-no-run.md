---
slug: harness-answer-without-code-no-run
track: harness
title: an answer that only decides scheduling (lift a hold) sends the change to dev
  and qa again
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T02:34:20Z'
---
sweep-24 P2-a, now seen: the user's answer-2 on central-token-login-op and server-token-auth ('... 1. Lift the hold', 2026-11-01) made both 'dev run due: the user answered after the hand-over'; central-token-login-op-7 handed over the same head 0485930ff with no code change (answer-2 'is a decision about when the change ships, not about the code'), and qa run -8 was then listed to re-judge the unchanged head. An answer that changes no row (a hold lift, a harness decision) records no dev step; only an answer that adds or changes a row does.
