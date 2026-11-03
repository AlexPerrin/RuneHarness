---
slug: harness-device-login-dialogs
track: harness
title: device_login does not handle the terms dialog and can tap links
kind: change
priority: P0
deps:
- harness-device-network-block
- client-login-index-log
created: '2026-11-01T01:10:05Z'
closed: 'answer-1: The user made devtools login the single path; tap-based dialog handling in device_login.py is superseded by client-devtools-login.'
---
tools/device_login.py's fixed taps do not handle the terms dialog that a fresh install shows, and one tap landed on a link that opened Chrome. Act on readable screen facts (logcat lines or devtools state) per dialog, never tap near a link, and keep every step bounded by an observed fact. Related: the client-launch-dialogs and client-devtools-login changes. Evidence: evidence/harness-no-powershell/proof.md (harness-no-powershell-2). One test per requirement touched.
