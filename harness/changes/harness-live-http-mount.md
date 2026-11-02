---
slug: harness-live-http-mount
track: harness
title: 'Live redeploy fails: http container''s jav_config.ws.template bind mount is
  a directory'
kind: change
priority: P0
mechanism: server
deps: []
created: '2026-11-02T16:09:40Z'
limit-of:
- client-login-segv-osclient
---
The first live redeploy after harness-live-deploy-on-tools-change shipped (ebbf4eb) failed 3 times since 16:04:13Z (state/live/ship.log): 'docker compose --env-file switch.env up -d --no-deps openrune http http-desktop issuer' exits 1 because osrs-openrune-http cannot start: error mounting .../docker-desktop-bind-mounts/... to /app/protocol/jav_config.ws.template: not a directory (the host source is missing, so Docker Desktop made a directory). osrs-openrune, issuer and http-desktop came up at the live pair's key 8555c56c; osrs-openrune-http is Exited (127). The bind source must be a file that exists before compose runs (written by ship, or from the record), and a failed ship should name the missing source. Evidence: state/live/ship.log

Also (filed): A failed live ship neither restarts the game server nor resets its strike count on a new key
Sweep 66 P1-b: compose up -d --no-deps openrune http ... recreates osrs-openrune before http fails, so every failed live ship restarts the live game server (state/live/ship.log: 19 'osrs-openrune Recreated', 30 'ship of ... failed'). hd.py:1325 resets the strike record p={} whenever args or key change; each newly gated server change moves the integration key, so the 3-strike cap reset at 16:04, 16:11, 16:40, 17:14Z and never converges on a key-independent fault. Count failures per cause (the failing step), and start the game server only once the rest of the stack starts. Evidence: state/live/ship.log, evidence/monitor/sweep-66.md

Also (client-login-segv-osclient): The live stack's record carries no modulus while every live ship fails, so no client up can log in
Seen by run client-login-segv-osclient-4 (2026-11-02 18:2xZ): 'tools/track.sh up client-login-segv-osclient' refuses APK fef4307c9fc5-be9887a9ab44 (modulus 8555c56c, the live pair's) with 'the live stack (state/live/tree.json) none, deployed before its key pair'. state/live/tree.json (written 2026-11-02 01:09) has no modulus because every live ship since 16:04Z fails at the http container's jav_config.ws.template bind mount (state/live/ship.log), while osrs-openrune itself runs at 8555c56c and osrs-openrune-http is Exited, so the app has no jav_config at :8080 either. The live stack must come up whole at its key pair and record that modulus in state/live/tree.json; then a client up of the live build can reach LOGGED_IN (the SEGV of this change no longer reproduced in run 3, whose login failed only on 'Invalid RSA check').
