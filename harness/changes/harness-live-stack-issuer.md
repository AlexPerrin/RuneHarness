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

Also (filed): STAFF=N makes only one account an administrator
sweep-44 P2-a: server-clan-channels-5 needs cheats on several accounts; STAFF takes one desktop (tools/track.sh:192 rights=... account "${STAFF:-0}"), so it re-upped the whole stack once per account (STAFF=2 05:48:12Z, STAFF=3 05:51:30Z, ~2.5 min each, desktops moving between instances). STAFF takes a list of desktops. evidence/monitor/sweep-44.md

Also (filed): a fresh account's login gets no inventory (container 93) from the run's server
sweep-45 P1-a and sweep-43 P1-a: server-clan-guest-3 (desktop_login.py 7787, fresh DB, STAFF=1, ~05:59Z) and cannon qa -8 (05:22Z) both reached LOGGED_IN with interface 149 visible but no inventory slots and list_inventories empty; no server exception; the client logs AIOOBE -1/1100 at 05:59:26Z (also seen on a working login). The login hang is fixed (up-owns-its-instance -2); the cause is not: find why the run's server sends no container 93 (or no slot build) at such a login, and fix it. Evidence: state/server-clan-guest/desktop8.log, evidence/monitor/sweep-45.md, sweep-43.md
