---
slug: harness-joined-finding-not-users-answer
track: harness
title: a finding joined after the hand-over is read as the user's answer and throws
  away a passing gate
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T01:14:21Z'
---
sweep-15 B1: hd new --blocks / --mechanism join records the finding as an answer row on the target; hd.py:1278 late_answers reads it as 'the user answered after the hand-over' and makes a dev step (hd.py:1297-1301). harness-build-gate-keyed-process passed its batch gate (T 8fcb253ca, 00:57:53Z), then the B6 join at 00:57:42Z made 'dev run due: the user answered after the hand-over (answer-3)' at 00:58:12Z and it did not ship. A joined finding and the user's word share one record: only the user's word reopens a handed-over head; a joined finding becomes scope the next hand-over takes (or its own change on the shipped head) without invalidating a gated head. evidence/monitor/sweep-15.md
