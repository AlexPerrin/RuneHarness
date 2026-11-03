---
slug: harness-limit-not-into-blocked
track: harness
title: A limit filing does not join a change that is waiting on its own deps
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T20:38:31Z'
---
Sweep 82 P2-a: server-clan-guest-6 filed the 7790 port limit at 20:32:19Z (state/events.jsonl:11252-11253, 3e988d7); it joined harness-desktop-one-login-path, which has waited on client-devtools-login since 2026-11-02T00:00:02Z and never started (chain: client-devtools-login -> harness-mobile-up-by-facts -> client-login-segv-osclient -> harness-live-stack-issuer -> harness-desktop-relogin-js5, server-token-refusal-logged). It now holds 8 joined desktop filings, none startable, and server-clan-guest waits on it (11256). The join (hd.py:3482) picks any open same-mechanism change with no dependency order to the filing and never checks whether it waits on its own deps. An unblocked limit is not joined into a waiting change: it stands as its own change ahead of it, or the waiting change is split. Evidence: evidence/monitor/sweep-82.md
