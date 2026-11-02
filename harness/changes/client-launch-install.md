---
slug: client-launch-install
track: harness
mechanism: mobile
title: 'up: install the APK only when the device''s copy differs'
kind: change
priority: P1
goal: client-launch
units:
- launch:install
created: '2026-11-01T01:01:19Z'
deps: [harness-device-network-block, harness-no-powershell, client-launch-measure]
superseded: harness-mobile-up-by-facts
---
up.ps1:32-36 uninstalls and fully reinstalls the APK on every up, even for the tree-cached build. Compare the installed package's APK digest (pm path + sha256sum on the device) with state/build.json's and install -r only when they differ; keep the libosrsrl check and the Chrome local network grant. The APK still always goes through the telemetry patch with OPENRUNE=1 LOCAL_AUTH=1. Proof: a second up on the same tree shows no install step in the client-launch report. Marks launch:install.
