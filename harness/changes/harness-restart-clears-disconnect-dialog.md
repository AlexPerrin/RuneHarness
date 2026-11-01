---
slug: harness-restart-clears-disconnect-dialog
track: harness
title: restart logs desktops back in past the disconnected dialog
kind: change
priority: P0
deps: [harness-desktop-login-devtools]
created: '2026-11-01T10:55:11Z'
---
central-login-whitelist-binds-2: during 'track.sh restart' the desktop sat behind the 'You were disconnected from the server' dialog, which keys do not close, so desktop_login.py never finished; the dev stopped it, clicked Ok with the devtools click tool and logged in by hand. Expected: restart (and any relogin) closes that dialog through the devtools (click its Ok) before the login, and ends on LOGGED_IN or the login's refusal. Overlaps harness-desktop-login-devtools (login through the client, no keys); land it there if that change takes it. One test per requirement touched.
