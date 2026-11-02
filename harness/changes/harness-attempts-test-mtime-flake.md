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
