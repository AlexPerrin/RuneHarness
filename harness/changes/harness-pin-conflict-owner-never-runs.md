---
slug: harness-pin-conflict-owner-never-runs
track: harness
title: A pin's integration conflict reaches a dev run or an alert
kind: change
priority: P0
deps: []
created: '2026-11-01T03:43:19Z'
---
The permanent pin fix/22-music-tab-play conflicts in the integration tree and blocks every server change's test server deploy, with no run working on it and no alert. Evidence: state/events.jsonl lines 1564 (02:05:25Z) and 1956-1958 (03:31:23Z): genie-review-355 and server-world-entities 'test server deploy blocked by fix/22-music-tab-play's conflict'; hd tick --dry-run at 03:4xZ still shows both blocked, and no change carries the owner's step 'pin fix/22-music-tab-play conflicts with the integration tree ...: dev'. harness-pin-base-conflict (done 02:15:22Z) added the base as a resolution partner, but hd.py integration() hands a pin's conflict to the oldest gated change (owner = ch or next(...)), and ship_test() dispatches the owner's dev step only when the owner itself reaches ship_test; any other change sees tint['change'] set and only records the block, and the alert fires only when change is None. When the owner is in another state (review due, gate, waiting) nothing ever runs. Make a pin's conflict always end in a dev run (or one alert when no change can own it), whatever state the owner is in. One test per requirement touched.
