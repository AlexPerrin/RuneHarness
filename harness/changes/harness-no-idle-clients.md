---
slug: harness-no-idle-clients
track: harness
title: A run keeps a game client up only while it plays in it
kind: change
priority: P1
deps: []
created: '2026-11-01T11:39:33Z'
---
The user (2026-11-01): 5 of 6 open RuneLite clients were idle. Each belonged to a live run (quest-sheepshearer-4, hunter-feat-pr-8, server-npc-examine-without-overlay-2, quest-runemysteries-11 x2, central-login-whitelist-binds-3) that had brought its desktops up and then spent long stretches building, reading code or writing. Expected: the dev and qa role text and track.md say a run brings a client up when it is about to act in game and runs down (or a cheap per-desktop stop that keeps the server) when it stops playing; the pass or the bridge notices a desktop of a live run with no devtools call for a stretch and tells the run once. Keep the no-cap rule; this is about idle time, not count. One test per requirement touched.
