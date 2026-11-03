---
slug: harness-dupe-tests-row-scope
track: harness
title: The dupe-tests seed row ignores a change whose tests the user dropped
kind: change
priority: P0
deps: []
created: '2026-10-31T23:50:49Z'
---
On cannon-review-354 the dupe-tests seed row requires test sources in dwarven-mine and dwarf-multicannon. The user's v6 decision 7 dropped #354's tests, so the row can never pass and the dev had to ask (cannon-review-354-2). A seed row must yield to a decision the user recorded for that change, or the change must be able to waive a seed row with the user's word. One test per requirement touched.
