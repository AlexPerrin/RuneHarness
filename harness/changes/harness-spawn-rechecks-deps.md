---
slug: harness-spawn-rechecks-deps
track: harness
title: A listed spawn is dropped when its change stops being due
kind: change
priority: P1
deps: []
created: '2026-11-01T04:05:56Z'
---
Observed: hd listed spawn server-token-auth-3 (dev) while the same hd output showed 'server-token-auth [server P0]: waiting on central-token-login-op' (after hd new central-token-login-op --blocks server-token-auth added the dep). Reruns kept listing the spawn; the brief state/briefs/server-token-auth-3.md stayed. The orchestrator ended it with hd stop server-token-auth-3. Expected: hd lists a spawn only for a change whose next step is a run, on the current definitions. One test per requirement touched.
