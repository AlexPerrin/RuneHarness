---
slug: harness-server-stack-deploy
track: harness
title: 'One deploy of the test-server stack: each instance (live or a run''s) and
  each attempt rendered from one declaration in tools/server'
kind: change
priority: P1
deps:
- harness-build-gate-keyed-process
- harness-issuer-official-shapes
- server-token-auth
mechanism: server
created: '2026-11-02T00:46:49Z'
---
Root cause (PRD workflow: a change's stack is deployed so QA and the user test it; the live server runs what was carried): the server stack's facts are scattered across ship, track.sh up and docker-compose.yml, keyed by build tree instead of by instance and attempt, so each new requirement (evidence, cache, idle logout, token issuer) patched one path. One deploy step renders the stack for an instance (live | run) and an attempt from tools/server, and ship and track.sh up both call it.

Carries: harness-live-issuer-cutover's tools commit 67cf143 (T 4a13623) and harness-live-deploy-evidence's joined idle-logout work (6ef5218).

Acceptance (all of the superseded changes):
1. Each deploy attempt writes build-<tree>-<attempt>.log and its failure line is in state/live/ship.log; the cache volume is shared across build trees, keyed by cache version (no 16 min re-download on a retry); the cause of today's 13 first-attempt 'build failed' lines is found and fixed; a test covers two attempts keeping two logs. (Evidence: integration ee13b4cf / live b5e0bddbc attempt 1 failed 22:08:13-22:09:21Z, attempt 2 overwrote its log.)
2. A run's own server starts with idleLogout off; the live server keeps the official idle logout; a test checks the run's rendered game.yml. (Evidence: genie-review-355-131 desktops 3 and 4 logged out 00:19:59Z and ~00:21:01Z, 5 min after last input, server up.)
3. The live stack takes the APK's tokens from issuer.py with its DIR mounted; served jav_config params 11, 20, 22, 28 point at it; game.yml token-login holds its secret; the sidecar runs with LOCAL_AUTH false. Proof: the APK (OPENRUNE=1 LOCAL_AUTH=1) logs in on a change's stack through the issuer, contacting only local hosts. It changes a live component: before ship, hd ask the user for a yes on the cutover.

The change waits on all three deps (part 3 needs server-token-auth and harness-issuer-official-shapes).

Also (filed): server track.md calls the desktop token login auth type 7; rsprot decodes token login as auth type 2
server-token-auth-13 hand-back: ~/src/OpenRune-Server/.worktrees/harness/tools/track.md:64 says 'login (auth type 7)'. rsprot 241 GameLoginDecoder decodes token login as auth type 2 (server-token-auth-12 QA FAIL on the same fact, fixed at e40d5e9dd). Fix the harness doc to auth type 2. (Lost in planner-18's merge of harness-live-deploy-evidence.)

Also (filed): a qa run's up built a tree other than the gated T
sweep-14 B7: state/genie-review-355/build-52b39cc9*.log 00:45:37Z: "Cannot locate tasks ':or-cache:qaCacheToolsClasspath'" after 'STAFF=1 tools/track.sh up genie-review-355 2'. The gated T is 286823c78 (T: genie-review-355 fc58c24e0 onto d30985ba3); 52b39 lacks main's newer files (ObjTakePluginTest.kt). Root cause unconfirmed: trace how up's tree gets its T. evidence/monitor/sweep-14.md

Also (filed): a build outside the current tools asked for a removed task
sweep-15 B5 follow-up to sweep-14 B7: up takes T from state/<slug>/build.json (server tools/track.sh:139), 286823c78 for genie-review-355, image exists. The failed build-52b39cc9 (00:45:37Z, .worktrees/genie-review-355-build) asked for :or-cache:qaCacheToolsClasspath, removed in 3db4e240a (2026-10-31); no current tools copy names it. Find who invoked it (the qa agent or a stale tools snapshot). evidence/monitor/sweep-15.md

Also (filed): a run's server still runs with idleLogout=true
server-friends-chat-clan-channels-20 hand-back (qa, T f79a9c77f): its own server config still has idleLogout=true, after 6ef5218 ('a run's server never idle-logs out its clients'); its desktop idled out and hung on relogin. The idle-logout acceptance here must hold live on a run's track.sh up. Evidence: evidence/server-friends-chat-clan-channels/in-game.md (Run 20)

Also (filed): a qa run's client sits at the login screen after an idle logout
The user (2026-11-01 ~20:3x ET): 'genie qa has been sitting at the loggin screen, after idle logged out for 20+mins' (genie-review-355-cickwdoqbbpt88aaaabeelmng-1, since 00:47:13Z). Same as server-friends-chat-clan-channels-20 (idleLogout=true on its server, desktop hung on relogin). A run's server must not idle-log out its clients, and a logged-out client must come back by facts, not wait.
