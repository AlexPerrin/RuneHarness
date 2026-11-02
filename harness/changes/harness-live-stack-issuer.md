---
slug: harness-live-stack-issuer
track: harness
title: The live stack takes the APK's tokens from issuer.py
kind: change
priority: P1
deps:
- server-token-auth
- harness-deploy-survives-tools-ship
- harness-mobile-login-by-facts
mechanism: server
created: '2026-11-02T03:15:21Z'
---
Planner-24 split of harness-server-stack-one-deploy by root cause: its deploy acceptance (3, 5, 6) joined harness-deploy-survives-tools-ship (one deploy step keyed by tree and tools); 1 and 2 moved to harness-qa-login-idle earlier; what remains is the issuer cutover, ordered after server-token-auth. Acceptance (its 4): the live stack takes the APK's tokens from issuer.py with its DIR mounted; served jav_config params 11, 20, 22, 28 point at it; game.yml token-login holds its secret; the sidecar runs with LOCAL_AUTH false. Proof: the APK (OPENRUNE=1 LOCAL_AUTH=1) logs in on a change's stack through the issuer, contacting only local hosts. It changes a live component: before ship, hd ask the user for a yes on the cutover. Carries harness-live-issuer-cutover's tools commit 67cf143 (T 4a13623).
