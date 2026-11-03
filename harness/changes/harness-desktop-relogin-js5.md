---
slug: harness-desktop-relogin-js5
track: harness
title: 'A desktop''s login more than 30 s after its last cache request gets its inventory:
  up''s second login, restart and the keepers'
kind: change
priority: P1
mechanism: desktop
limit-of:
- harness-live-stack-issuer
deps: []
created: '2026-11-02T19:39:21Z'
---
Joined harness-live-stack-issuer as answer-4 (server-world-entities-14: up 2's second login FAILED 'no inventory (container 93)' twice, passed the third time, no server log). Reproduced by harness-live-stack-issuer-2 (state/harness-live-stack-issuer/relog2.log): up's second round repeated on one stack (logout, offline, members update, login) fails on round 6 with interface 149 visible and 149:0 holding no dynamic children for 40+ ticks after the 10-tick bound, no inv 93 in the client, no server error; 61 quick logout-login rounds without the offline wait never fail (relog.log). The cause is evidence/harness-relogin-inventory/cause.md's: the server closes a logged-out client's JS5 connection after 30 s idle (rsprot's default idle handler), and the login's interface onLoad scripts run before the re-requested cache groups arrive (AIOOBE -1/1100 in prayer_init and magic_spellbook_init). The server sends inv 93 and opens 149 in the official order (reader: LoginScript.kt:125-135, PlayerInvUpdateProcessor.kt:55-59). This is the desktop login path's open case (harness-desktop-one-login-path: 'track.sh restart logs every desktop back in'), so it joins it. Acceptance: up 2's second login, restart and a keeper's relogin after more than 30 s logged out each end LOGGED_IN with the widget showing container 93.
