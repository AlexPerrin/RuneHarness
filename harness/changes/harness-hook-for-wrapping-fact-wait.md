---
slug: harness-hook-for-wrapping-fact-wait
track: harness
title: The counted-sleep rule denies a for loop that wraps a wait on a fact
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T07:23:57Z'
---
Monitor sweep 53 P3-b: deny_time_bound (hook.py:441) denies any for loop whose body sleeps, including `for p in 7780 7781; do until <fact on p>; do sleep 2; done; done`, which has no time bound (reproduced with the rule's regex; relogin-inventory-2's burst.sh has this shape). Acceptance: a sleep inside an until/while loop on a fact is allowed whatever loop encloses it; a counted or paced sleep stays denied.
