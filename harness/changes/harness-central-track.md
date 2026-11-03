---
slug: harness-central-track
track: harness
title: The harness can carry changes to OpenRune-Central-Server
kind: change
priority: P0
deps: []
created: '2026-11-01T03:35:13Z'
---
server-token-auth needs a change to OpenRune/OpenRune-Central-Server (dev.or2 2.0.2): a token LOGIN op on the world link (the user chose a Central PR plus a server PR). The harness has only client, server and harness tracks and no repo entry for Central. Add Central as a track in hd.yaml (upstream OpenRune/OpenRune-Central-Server, a fork under AlexPerrin, a local clone), with its own tools/track.sh (build, test, gate) and seed rows, and a way for the server's test build to use a locally built Central (the dev.or2 version the server depends on). Same rules as the server track: fork staging, one upstream PR per change, the user's yes on each card. One test per requirement touched.
