---
slug: harness-hold-p3-while-higher-open
track: harness
title: Runs follow the user's five priority tiers; a lower tier waits while a higher one is open
kind: change
priority: P0
deps: []
created: '2026-11-01T12:42:58Z'
---
The user's words: "No quests are p3, focus on higher priority work", then the order: "1. Harness fixes 2. Harness improvements (login) 3. Our upstream changes 4. Clans other in progress feature work 5. new quests."

The loop spawned P3 quest runs (quest-childrenofthesun, quest-ernestthechicken, quest-sheepshearer, quest-runemysteries) into free slots while higher changes were open but waiting on dependencies; the user stopped them by hand three times. Today PRIO has four levels (hd.py:24) and harness fixes share P0 with the login chain.

Acceptance:
- Five levels P0-P4, mapped to the user's order: P0 harness fixes; P1 harness improvements (the login chain: harness-desktop-login-devtools, client-devtools-login, server-token-auth, central-token-login-op, harness-live-issuer-cutover, client-launch-*, the devtools review gaps); P2 our upstream changes (PR reviews and their findings, hunter-feat-pr); P3 clans and other in-progress features; P4 new quests. The open definitions under harness/changes are retiered to match.
- hd lists no spawn for a change while a change of a higher tier is open (not closed), waiting or not, except a change that a higher open change depends on (it already inherits that tier). A test covers: lower held while higher waits; a dependency of a higher change still spawns; lower spawns once no higher is open.

The user's word: "all harness track changes are atleast P1". A harness-track change is never below P1, including one made by `hd new` without --priority.

The user's word on the harness tiers: "a fix is something blocking, P1 is for nonblocking (login flow works but, would significantly reduce time to P2)". P0 = a harness fix that blocks work; P1 = a non-blocking harness improvement (the work proceeds without it, but it significantly reduces the time to reach the P2 work).
