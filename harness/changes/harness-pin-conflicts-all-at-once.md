---
slug: harness-pin-conflicts-all-at-once
track: harness
title: A pin-conflict pass names every conflicting pin at once
kind: change
priority: P1
deps: []
created: '2026-11-01T04:18:47Z'
---
genie-review-355 runs 7, 8 and the listed 9 each resolved one pin conflict, after which hd reported the next: fix/22-music-tab-play and fix/25-ice-mountain-music-area (run 7, which reported every merge applied cleanly by hand in hd.yaml order), then fix/71-item-config-tradeable vs fix/59/63/70 (run 8), then content/pirates-treasure vs content/witchs-potion, content/genie, feat/hunter (run 9). One dev run per conflict. Expected: the integration check lists every pin that conflicts with the integration tree in one pass, so one run resolves them all; and the dev's by-hand check reproduces hd's merge order. One test per requirement touched.
