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
