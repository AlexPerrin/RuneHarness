---
slug: harness-dep-cycle-alert
track: harness
title: A dependency cycle among open changes is an alert, never a silent wait
kind: change
priority: P0
deps: []
created: '2026-11-01T20:56:50Z'
---
Found 2026-11-01 by the orchestrator on the user's 'Check that the queue hasn't deadlocked': central-token-login-op -> harness-desktop-login-devtools -> client-devtools-login -> server-token-auth -> central-token-login-op; every change in it showed 'waiting on X' with no alert. Broken by removing central-token-login-op's dep (d274f58). Earlier today cannon-review-354 and cannon-354-reset-ammo-varp deadlocked the same way. Acceptance: the pass finds every cycle in the deps of open changes and raises one alert naming the cycle; a change in a cycle is not shown as plain 'waiting on'; hd new and a definition commit refuse a dep that closes a cycle; a test covers both.
