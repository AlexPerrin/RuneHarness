---
slug: harness-desktop-instance-race
track: harness
title: Two server runs can take the same desktop client
kind: change
priority: P0
deps: []
created: '2026-11-01T01:47:03Z'
---
cannon-review-354-6: track.sh up cannon-review-354 4 raced the genie-review-355 run for desktop instance 2, and the cannon qa then acted on genie's client (devtools 7781, account ha8a368b702): it relogged, teleported, spawned cannon parts and tried Set-up. It undid what it could, but three spawned parts were left on the ground at (3257,3277) on genie's server. Two causes: (1) desktop instance allocation is not exclusive across concurrent ups; take each instance under a lock until up.json records it, the same way harness-device-boot-failure-cleanup locks emulator ports; (2) up aborts under set -e when one client fails to log in and leaves no up.json, so a run cannot tell which clients are its own. Write up.json as each client starts, and have down stop exactly those. Evidence: evidence/cannon-review-354/handoff.md. One test per requirement touched.
