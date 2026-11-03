---
slug: harness-server-realm-like-live
track: harness
title: A test server's realm gives players live ranks, not dev admin
kind: change
priority: P1
deps: []
created: '2026-11-01T05:28:23Z'
---
server-friends-chat-clan-channels-9 hand-back: a fresh database is a dev realm, which makes every player an administrator (rank 127). Rank-dependent rows (friends chat, clan ranks, kick) cannot be judged until the judge hand-edits realms.dev_mode=0 and the accounts' members flags with the players logged out, then track.sh restart. Accuracy requires the test server to behave like the official one. Expected: up creates the realm with dev_mode off and tester accounts as normal players (members per the change's needs), with an explicit per-run option for a staff account where a row needs one. Proof: a fresh up's two tester accounts log in at rank 0 and see each other's friends-chat ranks as on live. One test per requirement touched.
