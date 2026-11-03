---
slug: harness-ship-sidecar-data-env
track: harness
title: Ship passes the sidecar data dir to docker compose, so the live stack comes
  up
kind: change
priority: P0
deps: []
created: '2026-11-01T12:32:28Z'
---
The live ship of integration cecbe4f1b (state/live/proc-ship.json, attempts 2, 2026-11-01T12:21Z) built and cached or:9638f309c, then compose failed twice (state/live/ship.log):
  level=warning msg="The \"SIDECAR_DATA\" variable is not set. Defaulting to a blank string."
  invalid spec: :/data:ro: empty section between colons
hd alerts 'live: ship died twice without a result (state/live/ship.log)', and 7 changes sit at 'test server: deploying 9638f309c' (cannon-review-354, genie-review-355, goblin-diplomacy-review-367-fftgsrq, server-friends-chat-clan-channels, server-world-entities, quest-cooksassistant). Cause: the fork's tools/track.sh sets the shell variable sidecar_data=${SIDECAR_DATA:-$HOME/src/openrune-work/server-tools/sidecar/data} (line 39) but runs 'docker compose --env-file switch.env up ... openrune http http-desktop' (lines 290, 296) without SIDECAR_DATA in its environment, while tools/server/docker-compose.yml mounts "${SIDECAR_DATA}:/data:ro". Expected: ship (and its rollback) give compose the same sidecar data dir the script resolves, whatever the caller's environment; ship of 9638f309c reaches a result and the alert clears. A fix to the fork's local/harness tools, carried on harness/<slug>. One test per requirement touched.
