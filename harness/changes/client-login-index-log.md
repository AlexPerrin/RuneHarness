---
slug: client-login-index-log
track: client
title: The host logs the login screen's page, so device_login can act on it
kind: change
priority: P0
deps:
- harness-device-network-block
created: '2026-11-01T01:44:47Z'
---
device_login.py (harness-device-login-dialogs) cannot read which page the canvas login screen shows: on a fresh install the terms dialog (Accept / Decline, with privacy-policy and EULA links in its text) is drawn on the canvas, uiautomator sees nothing, devtools get_client_state has no login index, and a fixed tap landed on a link and opened Chrome on legal.jagex.com (evidence/harness-no-powershell/proof.md, client-login-screen.png). The host already reads the page (AndroidClient.getLoginIndex -> Native.loginIndex, desktop numbering 0-14). Log it: one osrsrl-host line 'LoginIndex <n>' each time the value changes while the game state is LOGIN_SCREEN (and once on entering LOGIN_SCREEN), from the client loop. Record in docs/client-state.md which index each Android page has (the terms dialog, the welcome page with Sign in / Play now, any other first-run page) and the canvas bounds of each page's buttons, read on the device. Proof: logcat of a fresh-install launch shows the LoginIndex line for the terms page and the next page. No call to Jagex servers.
