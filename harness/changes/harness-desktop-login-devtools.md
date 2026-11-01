---
slug: harness-desktop-login-devtools
track: harness
title: desktop login through the devtools login tool, no canvas clicks
kind: change
priority: P0
created: '2026-11-01T01:01:19Z'
deps:
- client-devtools-login
- harness-no-powershell
- harness-desktop-devtools-jar
---
docs/ISSUES.md: 'The desktop login still clicks the login screen. tools/server/desktop_login.py offsets fixed-mode points by the canvas size; RuneLite's login screen has no widget ids to act on. A devtools login tool in the client's devtools plugin would remove the last coordinates.' Once client-devtools-login ships the tool, desktop_login.py (fork local/harness) calls it and waits on get_client_state.gameState LOGGED_IN; delete the coordinate code and the ISSUES entry. Proof: one server up with the desktop clients logged in. One test per requirement touched.

From central-token-login-op-6: desktop_login.py hung when the server refused a login fast. The login ends on its outcome, success or a refusal reply (the login response code read from the client), never only on LOGGED_IN; a refused login returns the code and exits.

The user's word (2026-11-01, on harness-restart-clears-disconnect-dialog): no blind click on the login screen. This change also clears the 'You were disconnected from the server' dialog on every login and restart, only when the devtools read that dialog, by acting on its widget (never a fixed screen point: a mis-aimed click on 'New User' opens a browser to Jagex).

The user's word (2026-11-01): "Login was a pain point in v7, ensure our login automation is scripted and as quick as possible. Tie in with the token work to simplify the workflow, prefer devtools always." So: one scripted login path for every desktop and device, through the devtools login tool (no keystrokes, no screen points), fed by the compact token from the issuer (harness-desktop-token-login) where the server takes token logins and by the account's password otherwise; it ends on the devtools-read outcome (LOGGED_IN or the refusal code) with no fixed waits, clears the disconnected dialog through its widget, and up/restart/relogin all call that one path. desktop_login.py's keystroke code and the old mobile tap code are removed. Proof includes the time from client start to LOGGED_IN, recorded in evidence.
