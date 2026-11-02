---
slug: client-launch-measure
track: harness
mechanism: mobile
title: 'measure client-launch: launch-to-gameplay timeline from logcat and devtools'
kind: change
priority: P1
goal: client-launch
created: '2026-11-01T01:01:19Z'
deps: [harness-device-network-block, harness-no-powershell, client-devtools-login]
superseded: harness-mobile-up-by-facts
---
Goal client-launch (harness/goals/client-launch.md, inventory client-launch.json) has no measurement: tools/track.sh measure (track.sh:83-89) is the client-api probe only and records no timings. Make measure dispatch on GOAL: for client-launch, run up on a fresh emulator, log in the tester account on the test server, and write state/client-launch/measure.json {tree, value, report} with value = share of inventory rows in PASSES, and the report evidence/client-launch/measure.json: per unit, start, end and the fact that ended it, plus the total from logcat 'Start proc' of the app to the first game tick while LOGGED_IN. Timestamps only from the device's records (logcat -v epoch lines of ActivityTaskManager, PackageManager, osrsrl-host 'host starting'/'host ready'/'httpserver ... port'/GameStateChanged, devtools get_client_state); no sleep, estimate or timeout enters a number, and a step with no readable end is reported so. Also: write state/log-mark before login (track.sh:57 writes it after, so log hides the login) and print the devtools port from the httpserver line instead of the hardcoded 7780 (track.sh:58). Depends on harness-no-powershell: up.ps1 blocks every client up. Proof: two real measures, the report's steps in order with their facts. One test per requirement touched.
