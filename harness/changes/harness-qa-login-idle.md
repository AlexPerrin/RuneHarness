---
slug: harness-qa-login-idle
track: harness
title: a qa run's clients stay logged in and log back in on their own (no idle logout, no stuck login screen)
kind: change
priority: P0
mechanism: server
deps: []
created: '2026-11-02T02:35:00Z'
---
The user (2026-11-01, ET): "Fix logins and idling its impacting qa, spawn another dev agent P0 if needed." Earlier: "qa idles for 5 mins, and it' client logs out, it freezes at the login screen"; "genie qa has been sitting at the loggin screen, after idle logged out for 20+mins". Split out of harness-server-stack-one-deploy (its acceptances 1 and 2, which waited on server-token-auth) and harness-desktop-one-login-path (its two qa login defects, which waited on client-devtools-login), so it waits on nothing; both of those now depend on this change.

Cause: 6ef5218 only edited a definition; server tools/track.sh:152 (up) copies /app/game.yml out of the image (idle-logout: true, game.example.yml:33) and changes only the quest mode, so every run server idle-logs its clients out after 5 min (38/38 state/*/game.yml). tools/server/desktop_login.py runs only from up and restart (track.sh:176/184/192), so a logged-out desktop waits at LOGIN_SCREEN until a qa run restarts by hand.

Acceptance:
1. A run's own server (tools/track.sh up) starts with idle logout off; the live server keeps the official idle logout; a test checks the run's rendered game.yml.
2. A run's desktop that is logged out anyway (disconnect, restart, server restart) logs back in by facts (the login screen observed -> the run's login path), never waits at the login screen; a test covers it.
3. desktop_login.py (token or password) returns on a refusal screen: it presses "Try again" (or reports the refusal) instead of hanging (server-token-auth-14 worked around it with evidence/server-token-auth/qa9-try.py).
4. A run's first up that hits a WSL interop error and gets no desktop home copy retries or fails with the cause, never leaves a half-up instance (state/genie-review-355/up-134.log).

Evidence: genie-review-355-131 desktops 3 and 4 logged out 00:19:59Z and ~00:21:01Z; server-friends-chat-clan-channels-20 (evidence/server-friends-chat-clan-channels/in-game.md, Run 20); genie-review-355-cickwdoqbbpt88aaaabeelmng-1 at the login screen 20+ min; cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq-4 restarting its server by hand (~01:57Z); evidence/monitor/sweep-19.md, sweep-20.md.
