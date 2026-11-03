---
slug: harness-hook-writes-locked
track: harness
title: Every hook write of a run record happens under hd's state lock
kind: change
priority: P1
deps: []
created: '2026-11-01T21:24:37Z'
closed: 'answer-2: its lock paths were reverted; the answer is moot'
---
The user's word (2026-11-01): limits noted by harness-listed-run-not-dropped-1 'become new bugs'. That change (eb9660c) moved only hook.py bind() under hd.lock(); end_run and the other hook writes still save run records without the lock, so a pass's stale copy can overwrite them (or they overwrite the pass). Acceptance: every write of state/runs/*.json from hook.py re-reads and writes under hd.lock(); a test races each hook write against a pass.
