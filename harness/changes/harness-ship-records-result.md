---
slug: harness-ship-records-result
track: harness
title: A ship that completes records its result
kind: change
priority: P0
deps: []
created: '2026-11-01T18:19:58Z'
---
cannon-review-354 (2026-11-01, after the user's approval of 7a8b2331a): state/cannon-review-354/ship.log shows two complete runs of hd-public upstream (pushed 7a8b2331a to fork content/cannon; CI green at 7a8b2331a; commented, naming the head; PR #354 ready for review), and GitHub confirms PR #354 open, not draft, head 7a8b2331a, with the update comment present once. Yet hd raises 'cannon-review-354: ship died twice without a result' and the change stays 'shipping upstream'. So the completed public act left no result record, and the loop counts it as a death; a third attempt would repeat public acts. Acceptance: hd-public writes its result record atomically as its last step on success; the pass reads it and the change moves past shipping; a ship whose public acts are already observed done (head pushed, comment naming the head present, PR ready) records done without acting again; a test covers a ship that completes, and one already done upstream.
