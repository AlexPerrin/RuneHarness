---
slug: live-session-drops-after-login
track: fork
priority: P1
deps:
- h-fork-up-login-page
- server-reconnect
---
# The live server drops every session seconds after login (mobile on LoginIndex 9, desktop logged out), so no client probe completes

Repro 2026-11-07 13:00-13:29 EST, live stack (osrs-openrune up 11 h; http, http-desktop and issuer restarted ~12:50). Mobile (run 163, emulator-5560, APK tree 86485e2): login reaches LOGGED_IN at 13:00:40, then CONNECTION_LOST (raw 40) at 13:00:41, LOGIN_SCREEN LoginIndex 9. A fresh boot at 13:23: LOADING (raw 25) at 13:24:10, CONNECTION_LOST (raw 40) at 13:24:49, and mobile_login.py reports 'the server refused the login (LoginIndex 9)'. Desktop fallback (fork live-desktop, RSProx): logged in at 13:29:05, the api-probe plugin started, then '[osrs-test] logout' at 13:29:16 and no report. The server log (fork track.sh log live) has no line about any of these logins or disconnects; its last line is 17:59:41 UTC 'Cycle took too long'. The same APK stayed logged in at 04:27 today. Evidence: evidence/client-host-raw-gamestate/{measure-run.log,desktop-probe.log,logcat-host-drop.txt}. Done when a mobile up and a live-desktop each stay logged in until their down, and the server logs why it ends a session.
