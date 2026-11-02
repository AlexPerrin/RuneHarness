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

Also (filed): a filing the running dev was told about still counts as late
sweep-25 P2-a: build-host-fault-runners-2 (given 01:58:16Z) was sent answers 2-4 (02:08-02:17Z) by the orchestrator and its hand-over covers them, yet at 02:35:56Z answer-2..5 were listed as joined after the done head (late_answers hd.py:1323-1334 compares only with given). Record when a running dev is told a filing (the orchestrator's relay) and count it as taken. evidence/monitor/sweep-25.md

Also (filed): a missing upstream rule file reads as 'rules moved'
central-token-login-op-8: blob() returns '' for a missing file while the contract header writes 'absent', and the header's 'base' key is not a file path, so every key compares as moved when the last verdict has no rules field: a false 'upstream rules moved' re-judge of central-token-login-op (AGENTS.md, CONTRIBUTING.md, the PR template absent on upstream main; README.md 9b5785c7; base d694191). One format for an absent file, and 'base' compared as a sha.
