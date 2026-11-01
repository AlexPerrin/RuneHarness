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
