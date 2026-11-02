---
slug: harness-keeper-after-failed
track: harness
title: after a keeper's FAILED login nothing logs the desktop in again
kind: change
priority: P1
mechanism: desktop
deps: []
created: '2026-11-02T06:18:23Z'
---
sweep-46 P1-b: desktop_login.py keep() (fa658e pin ~164-180): r=FAILED while the client's gameState is LOGGED_IN; the retry loop exits, ready(since) is false, and the keeper waits for a LOGIN_SCREEN that never comes, leaving the desktop logged in with no inventory and no further keeper line; server-world-entities-11 has waited on it since 06:11:48Z. On FAILED the keeper logs out and retries (or ends and says so). Also (P2-a): the 10-tick check assumes the client's tick restarts at each login, but 7785 ran 0 -> 5 -> 97 across three logins; count from the first event after this login. evidence/monitor/sweep-46.md
