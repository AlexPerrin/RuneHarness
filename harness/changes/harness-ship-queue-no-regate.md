---
slug: harness-ship-queue-no-regate
track: harness
title: Approved, gated harness changes ship as one batch, not each re-gated after
  every sibling
kind: change
priority: P1
deps: []
created: '2026-11-01T21:52:41Z'
---
Monitor sweep 2 (2026-11-01 ~21:51Z): a harness change's merge commit T is built on the live v8 tip and one change ships per pass, so each ship invalidates the gates of every sibling waiting to ship: four were 'shipping' at 21:41:18Z and harness-hold-card, harness-spotless-check-row, harness-spawn-for-ended-run-refused and harness-hook-writes-locked were each built four times (e.g. hold-card a309467, 330b30f, d406de5, 424fae9); harness-conversation-bots-filtered went to 'tree conflict: dev' (docs/ARCHITECTURE.md) at 21:47:44 after a sibling shipped. Work grows with the square of the queue. Root cause: the gate is keyed to the exact v8 tip rather than to the combined result. Acceptance: all harness changes gated and ready in a pass merge together into one T, gated once and shipped once (a conflict or failure drops only the change that causes it, found by bisection); a test covers three ready siblings shipping in one gate.
