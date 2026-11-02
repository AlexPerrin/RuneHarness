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

Also (filed): A local change's contract gains the upstream PR rows (subject, texts) it can never pass
unseeded()/add_seeds() in hd.py write every seed row of the track's tools/track.md into a contract the track's rows lack, by id, whatever the change's kind. A kind: local change (server-world-entities: a test-only raft that never goes upstream, the user's answer) has no upstream PR, yet its contract gained subject (tools/server/text.py commits: feat:/fix: subjects) and texts (pr-body.md carries upstream's template sections). Its dev ref fork/dev/server-world-entities already holds f2a808495 'local: one static test raft world entity at Port Sarim' and the merge 488270104 'Merge origin/main into dev/server-world-entities', which cannot change without a forced push, so its gate fails at subject forever (gate log state/server-world-entities/gate.log). Root cause: the seed rows are the track's rules for an upstream PR, and the contract applies them to a change that opens none (upstream(ch) is false). Fix at the contract mechanism: a seed row that judges or checks the upstream PR's texts or commits applies only when upstream(ch) (mark those rows in the seed list, or seed a local change from a local subset), and remove them from server-world-entities' contract (subject, texts, and the PR-only judge rows no-deferral, net-change, one-change) so its gate reruns. One test per requirement touched.
