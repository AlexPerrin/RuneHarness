---
slug: harness-desktop-vsock-relaunch
track: harness
title: A WSL interop vsock failure fails the whole up, and it is frequent
kind: change
priority: P1
mechanism: desktop
deps: []
created: '2026-11-02T07:24:11Z'
---
Monitor sweep 53 P3-c: since keeper-after-failed shipped, a desktop launch that dies with '<3>WSL ... UtilAcceptVsock:273: accept4 failed 110' fails the whole up (as intended, no hang), but it is frequent: three in one up of server-clan-guest-4 (07:17Z, the third fatal); desktop logs holding only that line: quest-cooksassistant/desktop1 (11-01 23:44 local), hunter-feat-pr/desktop1 (00:32), server-clan-guest/desktop6 (07:17Z), server-clan-channels/desktop6 (07:01Z). Each costs a 1-2 min up rerun by hand. Acceptance: up launches that desktop again once the interop answers (an observed fact), and fails only when the launch fails for another cause.
