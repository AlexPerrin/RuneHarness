---
slug: harness-central-clone-identity
track: harness
title: The Central clone commits with the noreply identity
kind: change
priority: P1
deps: []
created: '2026-11-01T04:18:47Z'
---
central-token-login-op-2 hand-back: the snapshot commit inside Central's track.sh build failed with 'empty ident name' because ~/src/OpenRune-Central-Server has no git identity; the dev re-ran it with GIT_AUTHOR_*/GIT_COMMITTER_* set to the noreply identity. Every harness-made clone (or the track's build) commits as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com> with no per-run env. Proof: track.sh build in a fresh Central clone commits its snapshot. One test per requirement touched.
