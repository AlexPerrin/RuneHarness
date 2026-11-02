---
slug: harness-server-stack-one-deploy
track: harness
title: 'One deploy of the test-server stack, rendered per instance and attempt from
  tools/server: a run''s server never idle-logs out and its logged-out client logs
  back in'
kind: change
priority: P0
deps:
- harness-build-gate-keyed-process
- harness-issuer-official-shapes
- server-token-auth
mechanism: server
created: '2026-11-02T01:54:03Z'
---
Root cause (PRD workflow: a change's stack is deployed so QA and the user test it; the live server runs what was carried): the server stack's facts are scattered across ship, track.sh up and docker-compose.yml, keyed by build tree instead of by instance and attempt, so each new requirement (evidence, cache, idle logout, token issuer, relogin) patched one path, and 6ef5218 ("a run's server never idle-logs out its clients") only edited a definition, no code. One deploy step renders the stack for an instance (live | run) and an attempt from tools/server; ship and track.sh up both call it; a run's desktop that is logged out logs back in by facts.

Merges harness-run-idle-logout-off (P0, the user's split) and harness-server-stack-deploy (the user's word "merge", 2026-11-01). P0: every qa run's client freezes at the login screen. The user (2026-11-01, ET): "qa idles for 5 mins, and it' client logs out, it freezes at the login screen"; earlier "genie qa has been sitting at the loggin screen, after idle logged out for 20+mins".

Carries: harness-live-issuer-cutover's tools commit 67cf143 (T 4a13623), harness-live-deploy-evidence's idle-logout work (6ef5218). (harness-run-idle-logout-off-1 and -2 were stopped before any hand-over: no dev ref exists; the idle-logout work starts from 6ef5218's definition only.)

Acceptance:
1. A run's own server (tools/track.sh up) starts with idleLogout off; the live server keeps the official idle logout; a test checks the run's rendered game.yml.
2. A run's desktop that is logged out anyway (disconnect, restart) logs back in by facts (the login screen observed -> the run's login path), never waits at the login screen; a test covers it.
3. Each deploy attempt writes build-<tree>-<attempt>.log and its failure line is in state/live/ship.log; the cache volume is shared across build trees, keyed by cache version (no 16 min re-download on a retry); the cause of the 13 first-attempt 'build failed' lines is found and fixed; a test covers two attempts keeping two logs. (Evidence: integration ee13b4cf / live b5e0bddbc attempt 1 failed 22:08:13-22:09:21Z, attempt 2 overwrote its log.)
4. The live stack takes the APK's tokens from issuer.py with its DIR mounted; served jav_config params 11, 20, 22, 28 point at it; game.yml token-login holds its secret; the sidecar runs with LOCAL_AUTH false. Proof: the APK (OPENRUNE=1 LOCAL_AUTH=1) logs in on a change's stack through the issuer, contacting only local hosts. It changes a live component: before ship, hd ask the user for a yes on the cutover. (Needs server-token-auth.)
5. Server track.md:64 says 'login (auth type 7)'; rsprot 241 GameLoginDecoder decodes token login as auth type 2 (server-token-auth-12 QA FAIL, fixed at e40d5e9dd): the doc says auth type 2.
6. Trace how a qa run's up got a tree other than the gated T: state/genie-review-355/build-52b39cc9*.log 00:45:37Z "Cannot locate tasks ':or-cache:qaCacheToolsClasspath'" after 'STAFF=1 tools/track.sh up genie-review-355 2'; gated T 286823c78; up takes T from state/<slug>/build.json (server tools/track.sh:139); the task was removed in 3db4e240a; find who invoked it and fix it there. (evidence/monitor/sweep-14.md B7, sweep-15.md B5)

Evidence (idle logout): genie-review-355-131 desktops 3 and 4 logged out 00:19:59Z and ~00:21:01Z, 5 min after last input; server-friends-chat-clan-channels-20 (evidence/server-friends-chat-clan-channels/in-game.md, Run 20: idleLogout=true, desktop hung on relogin); genie-review-355-cickwdoqbbpt88aaaabeelmng-1 at the login screen 20+ min (stopped 01:19:38Z); cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq-4 (the user's report ~01:4xZ).

Also (filed): the server track.sh header also calls the token desktop auth type 7
server-token-auth-14 hand-back: besides track.md:64 (already filed here), the server tools/track.sh header says the token desktop sends 'auth type 7'; rsprot decodes token login as auth type 2. Fix both.
