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
---
The first live redeploy after harness-live-deploy-on-tools-change shipped (ebbf4eb) failed 3 times since 16:04:13Z (state/live/ship.log): 'docker compose --env-file switch.env up -d --no-deps openrune http http-desktop issuer' exits 1 because osrs-openrune-http cannot start: error mounting .../docker-desktop-bind-mounts/... to /app/protocol/jav_config.ws.template: not a directory (the host source is missing, so Docker Desktop made a directory). osrs-openrune, issuer and http-desktop came up at the live pair's key 8555c56c; osrs-openrune-http is Exited (127). The bind source must be a file that exists before compose runs (written by ship, or from the record), and a failed ship should name the missing source. Evidence: state/live/ship.log

Also (filed): A failed live ship neither restarts the game server nor resets its strike count on a new key
Sweep 66 P1-b: compose up -d --no-deps openrune http ... recreates osrs-openrune before http fails, so every failed live ship restarts the live game server (state/live/ship.log: 19 'osrs-openrune Recreated', 30 'ship of ... failed'). hd.py:1325 resets the strike record p={} whenever args or key change; each newly gated server change moves the integration key, so the 3-strike cap reset at 16:04, 16:11, 16:40, 17:14Z and never converges on a key-independent fault. Count failures per cause (the failing step), and start the game server only once the rest of the stack starts. Evidence: state/live/ship.log, evidence/monitor/sweep-66.md
