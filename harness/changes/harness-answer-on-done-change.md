---
slug: harness-answer-on-done-change
track: harness
title: An answer on a done or closed change reopens it (or is refused, naming why);
  it is never silently kept
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-01T22:59:21Z'
---
Monitor sweep 7: the orchestrator's 22:49Z answer on harness-answer-reaches-dev (done since 22:22:55Z) was kept as a row and nothing followed; cmd_answer (hd.py:2126) accepts an answer on a done or closed change without reopening or refusing. So the limit 'an answer QA already judged still forces a dev run' stays unfixed: genie-355-bank-lamp-5 ran again for nothing (22:47-22:49Z) and T 3694c018b was rebuilt and re-gated. Acceptance: hd answer on a done harness change reopens it (state back to dev run due with the answer) and on a closed one refuses with 'closed: file a change'; plus fix the carried limit: only an answer newer than both the hand-over and the last verdict on that head makes a dev run due (genie-355-bank-lamp answer-1, judged by qa-4, must not).

Also (filed): hd handover refuses a hand-back whose in-scope limit is stated in prose, not only as limit:<slug>; and every open definition is backfilled to one change per mechanism
Monitor sweep 9 (2026-11-01 23:13Z): the in-scope-limit refusal matches only 'limit:<slug>' tokens, so a limit in prose passes and the orchestrator bounces it back as an answer, costing another full run (harness-ship-queue-no-regate run 2, harness-docs-tree-conflicts run 1, whose script was left in a session scratchpad). And harness-mechanism-required (39b6ca0) landed without its backfill: harness-tools-pinned-per-process has no mechanism: line, and open changes per mechanism are mobile 5, build-gate 2, desktop 2, server 2. Acceptance: a hand-back states its limits in a required 'Limits:' section, each marked in-scope or limit:<slug>; hd handover refuses any in-scope entry; every open definition carries a mechanism; the planner merges the open changes sharing one (the user closes the superseded ones).

Also (filed): A seed row added later does not re-open a change already carried upstream at its head
Observed 2026-11-01 23:25Z: harness-spotless-row-complete shipped 'already-agreed contracts get the spotless row' (the orchestrator wrote that acceptance), so every carried change's contract hash changed and they all went to 'review due': cannon-review-354, the three cannon-354 replies, goblin-diplomacy-review-367-fftgsrq and quest-cooksassistant - six QA runs re-judging heads that are already upstream and unchanged. Root cause: a contract's new seed row invalidates verdicts on heads whose work is finished. Acceptance: a new seed row applies to a contract at its next head (a head not yet carried); a change carried at its live head keeps its verdict until its head moves; a test covers a seed row added after carry.
