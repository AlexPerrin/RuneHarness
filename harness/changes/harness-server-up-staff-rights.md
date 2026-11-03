---
slug: harness-server-up-staff-rights
track: harness
title: 'server up: STAFF=N leaves the Nth account without administrator rights'
kind: change
priority: P1
deps: []
created: '2026-11-01T06:17:48Z'
---
On the server track, `STAFF=1 tools/track.sh up quest-runemysteries 1` (OpenRune-Server tools branch, track.sh up(), line ~178) finishes with LOGGED_IN, but accounts.rights for hbdc551d621 reads '' afterwards (select account_name, rights from accounts), so every cheat (::tele, ::item) is silently refused (no message, position unchanged); plain chat reaches the server. A select of the same CASE expression yields ADMINISTRATOR, so the update's predicate is right: the value is lost after it, most likely the server's own save of the account at the logout that offline() waits for lands after the update (offline() waits on character_progress only). Requirement: after an up with STAFF=N, the Nth desktop's account is an administrator in game (::mypos answers) and every other account is not; a test in tests/ of the harness covers the ordering (rights written only after the account row's logout save, or rights read back and re-applied until they hold).
