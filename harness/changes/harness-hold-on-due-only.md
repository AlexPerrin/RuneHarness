---
slug: harness-hold-on-due-only
track: harness
title: A lower tier waits only while a higher change has a run due now
kind: change
priority: P0
deps: []
created: '2026-11-01T18:07:05Z'
---
The user's choice (2026-11-01): "Hold on due only". The tier hold (harness-hold-p3-while-higher-open) holds every lower tier while any higher change is open, waiting or not. With nine P1 changes all waiting on the login chain, no P2-P4 run spawns: genie-review-355's dev run (the owner of the content/looting-bag pin conflict, which blocks the test-server deploy of goblin-367, friends-chat/clan-channels and Cook's Assistant) and cannon-354-reset-ammo-varp's resume are both due and never listed. Acceptance: a change is held only while a change of a higher tier has a run due in this pass (a spawn it would list); a higher change that is waiting on a dependency, gated, or awaiting the user's yes holds nothing; the user's hold band in hd.yaml still applies; the R6 test covers: lower held while a higher run is due; lower spawns while every higher change only waits.
