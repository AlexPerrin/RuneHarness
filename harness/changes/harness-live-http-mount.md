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
