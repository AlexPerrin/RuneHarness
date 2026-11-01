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
deps: [harness-device-network-block, harness-mobile-devtools-jar, server-token-auth]
---
The Android login (tools/device_login.py:9,43-54) taps fixed coordinates SIGN_IN (1200,617), ACCEPT (1032,645), PLAY_NOW (1197,540), re-reads all of logcat every 3 s, and a missed tap waits forever (docs/ISSUES.md: 'A dev's tap on the emulator is never retried'). The desktop login (tools/server/desktop_login.py on the fork's local/harness) clicks fixed-mode points offset by the canvas (docs/ISSUES.md: 'The desktop login still clicks the login screen'). Add a login tool to the client's devtools plugin that performs the login through the client (the login state and its submit, no screen points) and returns the resulting gameState; device_login.py calls it and blocks on the streamed logcat line GameStateChanged LOGGED_IN (logcat -s osrsrl-host, no poll), and a step whose fact does not change is re-issued on that fact, not on time. Proof: client-launch report's login step ends on LOGGED_IN with no tap; ten consecutive logins succeed. Marks launch:login. The desktop script's switch to this tool is harness-desktop-login-devtools.

The user's word (2026-11-01): "Login was a pain point in v7, ensure our login automation is scripted and as quick as possible. Tie in with the token work to simplify the workflow, prefer devtools always." So: one scripted login path for every desktop and device, through the devtools login tool (no keystrokes, no screen points), fed by the compact token from the issuer (harness-desktop-token-login) where the server takes token logins and by the account's password otherwise; it ends on the devtools-read outcome (LOGGED_IN or the refusal code) with no fixed waits, clears the disconnected dialog through its widget, and up/restart/relogin all call that one path. desktop_login.py's keystroke code and the old mobile tap code are removed. Proof includes the time from client start to LOGGED_IN, recorded in evidence.
