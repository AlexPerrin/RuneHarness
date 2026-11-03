---
slug: harness-up-inventory-widget-empty
track: harness
title: After the server track's up, the desktop's inventory widget shows the inventory
kind: change
priority: P1
deps: []
created: '2026-11-01T13:13:35Z'
---
Hand-back of cannon-354-return-after-destroy-3: on the first 'track.sh up' the desktop's inventory widget stayed empty although container 93 held the items; 'tools/track.sh restart' fixed it. Non-blocking (restart works around it) but costs each in-game run a restart. Acceptance: after up, get_inventory's widget view matches container 93 on the first login; a check in up fails loudly when they differ.
