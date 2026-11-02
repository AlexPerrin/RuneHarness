---
slug: harness-run-idle-logout-off
track: harness
title: a run's server never idle-logs out its clients, and a logged-out client logs back in on its own
kind: change
priority: P0
mechanism: server
deps: []
created: '2026-11-02T01:55:00Z'
---
The user (2026-11-01, ET): "qa idles for 5 mins, and it' client logs out, it freezes at the login screen"; earlier "genie qa has been sitting at the loggin screen, after idle logged out for 20+mins". The user's yes (2026-11-01) to split this out of harness-server-stack-deploy as its own P0 change with no deps.

Cause: 6ef5218 ("a run's server never idle-logs out its clients") only edited a change definition; no code was written, and that acceptance then waited inside harness-server-stack-deploy on server-token-auth. Every qa run's client idle-logs out after 5 min and its desktop hangs at the login screen.

Acceptance:
1. A run's own server (tools/track.sh up) starts with idleLogout off; the live server keeps the official idle logout; a test checks the run's rendered game.yml.
2. A run's desktop that is logged out anyway (disconnect, restart) logs back in by facts (the login screen observed -> the run's login path), never waits at the login screen; a test covers it.

Evidence: genie-review-355-131 desktops 3 and 4 logged out 00:19:59Z and ~00:21:01Z, 5 min after last input; server-friends-chat-clan-channels-20 (evidence/server-friends-chat-clan-channels/in-game.md, Run 20: idleLogout=true, desktop hung on relogin); genie-review-355-cickwdoqbbpt88aaaabeelmng-1 at the login screen 20+ min (stopped 01:19:38Z); cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq-4 (the user's report ~01:4xZ).
