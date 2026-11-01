---
slug: client-devtools-login
track: client
title: devtools login tool; device and desktop logins act on it, not coordinates
kind: change
priority: P1
goal: client-launch
units:
- launch:login
created: '2026-11-01T01:01:19Z'
deps: [harness-device-network-block, client-launch-measure]
---
The Android login (tools/device_login.py:9,43-54) taps fixed coordinates SIGN_IN (1200,617), ACCEPT (1032,645), PLAY_NOW (1197,540), re-reads all of logcat every 3 s, and a missed tap waits forever (docs/ISSUES.md: 'A dev's tap on the emulator is never retried'). The desktop login (tools/server/desktop_login.py on the fork's local/harness) clicks fixed-mode points offset by the canvas (docs/ISSUES.md: 'The desktop login still clicks the login screen'). Add a login tool to the client's devtools plugin that performs the login through the client (the login state and its submit, no screen points) and returns the resulting gameState; device_login.py calls it and blocks on the streamed logcat line GameStateChanged LOGGED_IN (logcat -s osrsrl-host, no poll), and a step whose fact does not change is re-issued on that fact, not on time. Proof: client-launch report's login step ends on LOGGED_IN with no tap; ten consecutive logins succeed. Marks launch:login. The desktop script's switch to this tool is harness-desktop-login-devtools.
