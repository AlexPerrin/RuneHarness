---
slug: harness-relogin-inventory
track: harness
title: a character's second login on a run's server sometimes gets no inventory
kind: change
priority: P1
mechanism: server
deps: []
created: '2026-11-02T06:18:23Z'
---
sweep-45/46 P1-a: the failing login is a re-login of an account already logged in once on the same server (track.sh up logs in, logs out, waits offline, logs in again, fa658e pin track.sh:186-193): clan-guest ~06:11Z (FAILED after 10 ticks), world-entities' keeper 06:11:55Z (list_inventories count 0 at 06:15Z), cannon 05:22Z; other re-logins got theirs. No server exception. Find why the server sends no container 93 on such a login and fix it. Moved out of harness-live-stack-issuer, whose deps are held. Evidence: evidence/server-clan-guest/up1.log, state/server-world-entities/keep-7785.log, evidence/monitor/sweep-46.md

Also (filed): STAFF=N makes only one account an administrator
sweep-44 P2-a: server-clan-channels-5 needs cheats on several accounts; STAFF takes one desktop (tools/track.sh:192), so it re-upped the whole stack once per account (~2.5 min each). STAFF takes a list of desktops. Moved out of harness-live-stack-issuer, whose deps are held. evidence/monitor/sweep-44.md
