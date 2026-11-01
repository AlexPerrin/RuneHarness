---
slug: harness-ship-pushes-tools-branches
track: harness
title: Ship pushes the tools branches it moves
kind: change
priority: P2
deps: []
created: '2026-11-01T02:02:35Z'
---
The user's word: keep v8 and the tools branches pushed. Ship fast-forwards the fork's local/harness and the client's client/harness-v8 but pushes only the live harness branch. After a ship moves a tools branch, push it: the fork's local/harness to the remote named fork (AlexPerrin/OpenRune-Server), never to origin (upstream OpenRune), and client/harness-v8 to the client repo's origin. A plain fast-forward push, with no force. Both were pushed by hand on 2026-11-01. One test per requirement touched.
