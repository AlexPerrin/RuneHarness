---
slug: harness-restart-clears-disconnect-dialog
track: harness
mechanism: desktop
title: restart logs desktops back in past the disconnected dialog
kind: change
priority: P1
deps: [harness-desktop-login-devtools]
created: '2026-11-01T10:55:11Z'
superseded: harness-desktop-one-login-path
---
central-login-whitelist-binds-2: during 'track.sh restart' the desktop sat behind the 'You were disconnected from the server' dialog, which keys do not close, so desktop_login.py never finished; the dev stopped it, clicked Ok with the devtools click tool and logged in by hand. Expected: restart (and any relogin) closes that dialog through the devtools (click its Ok) before the login, and ends on LOGGED_IN or the login's refusal. Overlaps harness-desktop-login-devtools (login through the client, no keys); land it there if that change takes it. One test per requirement touched.

The user's word (2026-11-01): option B. The handed-over head (fork c109bbaee, a fixed-point click at 382,301) must not ship: its work moves into harness-desktop-login-devtools. Held behind that change until the user closes this one.
