---
slug: harness-attempts-test-mtime-flake
track: harness
title: R5 test_attempts_reset_on_new_args_or_a_landed_result fails at random
kind: change
priority: P1
mechanism: loop
limit-of:
- harness-filestore-track
deps: []
created: '2026-11-02T21:22:37Z'
---
The suite at T (harness-filestore-track cb682c3, a docs and hd.yaml change) failed once in R5.test_attempts_reset_on_new_args_or_a_landed_result: 'sum("ended 3 times" in a for a in ctx.alerts) 2 != 1' (tests/test_hd.py:2546); run alone in the same worktree it failed, then passed, at the same tree. The test writes track.sh and starts on it at once; ctx.start's 'the script is fixed' test (hd.py:1403 newer: the script's mtime_ns > proc-build.json's) races the mtime of the script against the proc record written in the same tick, so a raised start is sometimes taken as a fixed script and alerts again. Decide on a fact the test controls (the script's mtime set before the proc record, or the record's own field), not the clock tick. Evidence: state/harness-filestore-track/tests.txt

Also (filed): A dependent waits on the head it needs, not on joins its dependency collects later
Sweep 86 P2-a: server-token-auth-19's limit joined harness-tree-transitive-central at 21:12:49 (events.jsonl:11486-11487); its fix 60891e9 shipped as 46c090c ~21:21, but two other filings had joined the same change (answer-1 stacked direction 21:12:49; answer-2 harness-ci-keyed-on-tree 21:16:07, 11504, during run -1, handover given: 0), so run -2 was listed and server-token-auth and server-token-refusal-logged stay 'waiting on harness-tree-transitive-central'. deps_held (hd.py:1642-1644) 'joined and ctx.done(dep, dh)' holds every dependent until the dep's dev acts on scope it never needed. With one open change per mechanism every limit target collects joins. A joined filing holds only its change; a dependent's need is met once the head it waited on is live; only a user's late answer reopens it for dependents. Evidence: evidence/monitor/sweep-86.md
