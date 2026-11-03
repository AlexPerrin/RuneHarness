---
slug: harness-drop-hd-user-alert
track: harness
title: No alert for public acts running with the user's own token
kind: change
priority: P1
deps: []
created: '2026-11-01T18:09:53Z'
---
The user's word (2026-11-01): "hd-public acts on GitHub with your own token, that's fine with me." hd.py:592 raises 'user: R4: no Unix user hd; public acts run as you with your token' on every pass, which re-surfaces an accepted setup as an alert. Acceptance: the alert and the separate-Unix-user requirement are removed (PRD R4, ARCHITECTURE, hd.py, its test); public acts run with the user's token as the documented setup; the R4 tests still pass.
