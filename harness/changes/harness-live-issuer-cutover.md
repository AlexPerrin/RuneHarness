---
slug: harness-live-issuer-cutover
track: harness
mechanism: server
title: The live test stack takes its tokens from issuer.py, not the sidecar's LOCAL_AUTH
kind: change
priority: P1
deps:
- harness-issuer-official-shapes
- server-token-auth
created: '2026-11-01T11:39:06Z'
superseded: harness-server-stack-deploy
---
From harness-token-issuer-long-term (evidence/harness-token-issuer-long-term/plan.md). Once server-token-auth runs on the live server, the sidecar's unsigned lu- tokens are refused and the APK's login breaks. Change local/harness tools/server/docker-compose.yml: issuer.py runs on the live stack with its DIR mounted; the served jav_config params 11, 20, 22 and 28 point at it; game.yml token-login holds its secret; and the sidecar runs with LOCAL_AUTH false. The proof is the APK (OPENRUNE=1 LOCAL_AUTH=1) logging in on a change's stack through the issuer, with no host but local ones contacted. This changes a live component: before ship, hd ask the user for a yes on the cutover.
