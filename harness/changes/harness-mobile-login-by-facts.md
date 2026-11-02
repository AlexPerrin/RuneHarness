---
slug: harness-mobile-login-by-facts
track: harness
title: mobile_login.py never gets past the login screen
kind: change
priority: P1
mechanism: mobile
deps: []
created: '2026-11-02T04:22:32Z'
---
sweep-34 P1-a: client-login-segv-osclient-3 (emulator-5562) and harness-live-stack-issuer-1 both stuck: the app reaches LOGIN_SCREEN, then LoginIndex 12 and 30, never LOGGED_IN; mobile_login.py ran 12-13 min and the devs fell back to adb taps (540,2084) and screenshots. state/tools/44ef4314ef38/tools/mobile_login.py:49-55: after SIGN_IN it re-taps PLAY_NOW at the fixed landscape point (1197,540) every 3 s (its own comment says a tap is never retried), never reads LoginIndex, and the fixed 2400x1080 TAPS can miss. Log in by the client's login state (LoginIndex/GameState via devtools), each step ending on the observed next state. evidence/monitor/sweep-34.md
