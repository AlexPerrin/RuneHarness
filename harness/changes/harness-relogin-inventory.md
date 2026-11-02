---
slug: harness-relogin-inventory
track: harness
title: a character's second login on a run's server sometimes gets no inventory
kind: change
priority: P1
mechanism: server
deps:
- server-js5-idle-relogin
created: '2026-11-02T06:18:23Z'
superseded: harness-server-stack-one-record
closed: 'answer-3: superseded by harness-server-stack-one-record'
---
sweep-45/46 P1-a: the failing login is a re-login of an account already logged in once on the same server (track.sh up logs in, logs out, waits offline, logs in again, fa658e pin track.sh:186-193): clan-guest ~06:11Z (FAILED after 10 ticks), world-entities' keeper 06:11:55Z (list_inventories count 0 at 06:15Z), cannon 05:22Z; other re-logins got theirs. No server exception. Find why the server sends no container 93 on such a login and fix it. Moved out of harness-live-stack-issuer, whose deps are held. Evidence: evidence/server-clan-guest/up1.log, state/server-world-entities/keep-7785.log, evidence/monitor/sweep-46.md

Also (filed): STAFF=N makes only one account an administrator
sweep-44 P2-a: server-clan-channels-5 needs cheats on several accounts; STAFF takes one desktop (tools/track.sh:192), so it re-upped the whole stack once per account (~2.5 min each). STAFF takes a list of desktops. Moved out of harness-live-stack-issuer, whose deps are held. evidence/monitor/sweep-44.md

Also (joined): track.sh restart hangs: the restarted client never fills its inventory, NPC names read null
cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq-8 (qa, 2026-11-02): its first `track.sh restart` hung at the login step, which waits for the inventory widget to fill; on the restarted client it never did, and the client showed NPC names as "null" with no options. The run stopped the restart and used `down` + `RESUME=1 up` instead. Same symptom as a second login sending no container 93.

Also (filed): track.sh down loops forever when the server container is already gone
Monitor sweep 48 P1-b: `track.sh down server-clan-guest` (pid 2850649, tools 771f13a41350) loops in offline() since ~06:35Z: sql() takes the port from docker logs (track.sh:59-60) and runs psql with -p "" against container:server-server-clan-guest, which no longer exists (docker ps -a); offline() loops until count = 0 (track.sh:70) and down() checks the server only before the loop (track.sh:219). server-clan-guest-3 is blocked on it. Acceptance: down ends, on an observed fact, when the server is gone at any point.
