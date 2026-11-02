---
slug: harness-local-done-needs-verdict
track: harness
title: a local change whose head reached the live tree went done over a failed verdict
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T03:41:24Z'
---
server-world-entities (kind: local) had qa verdict FAIL 3 rows at 488270104 (server-world-entities-8: a5-range, accuracy, style); dev run -9 was fixing it when, at the 03:33:10Z live deploy, the pass marked the change 'done' (03:33:50Z, run ended 'change done') and then stopped the run's slice on every long command (exit 144). A local change is done only when its head is live AND its last verdict passes; a failed head is not in the live integration tree. evidence: state/events.jsonl 03:30:10-03:40:44Z; server-world-entities-9's hand-back.
