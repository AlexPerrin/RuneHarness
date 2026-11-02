---
slug: harness-gate-sigterm-is-host-fault
track: harness
title: A gate row killed by a signal (rc 143 'Terminated') reads as the head's failure,
  and the same head can never re-gate
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T07:22:35Z'
---
server-world-entities: its gate at T 8d0e20c4a failed row ci with out 'Terminated', rc 143 at 06:48:42Z (state/server-world-entities/row-gate-ci.json), killed by the tools test's host-wide pkill of 'sleep 30' (fixed in aa6b02e52). The pass sent it to a dev (runs -12, -13), both of which re-handed over the same head cab31a4c0 with no code change; the result stays keyed to that tree, so hd now alerts 'dev run server-world-entities-13 handed back its record, yet its step is still due on the same input: no run is listed'. hunter-feat-pr hit the same (rc 143, 06:36:13Z). Acceptance: a row ended by a signal is a host fault: the gate re-runs it rather than charging the head; a stale host-fault result never keeps a change on 'gate failed: dev'.

Also (filed): A gate row ended by a signal is recorded as the head's result and kept at its key
Fact: hunter-feat-pr's gate on 2d85512ea-21ec60df2-9686679aa (head 89632544d) ran its ci row (tools/track.sh gate-ci) at 06:34:41Z; at 06:35:02Z run hunter-feat-pr-19 ended and its processes were stopped, and the ci row exited 143 with 'Terminated' (state/hunter-feat-pr/row-gate-ci.json, key 2d85512eab32...-21ec60df216e-30b1204c4446). rows() in hd.py records every rc but HELD under the row's key and keeps it on every later gate of that key, so the re-handover of the same head (run hunter-feat-pr-20, 06:43:28Z) re-reported 'FAIL: ci ... Terminated' at 07:18:35Z without running CI, and the change goes back to a dev that has nothing to fix: a dev run per gate, forever, until the server tools or the head change. Root cause (R5/R8): a row's recorded result is the head's verdict on that row, but a row killed by a signal (rc > 128, or one whose process the pass or a run's slice stop ended) says nothing of the head; it is a host fault like HELD. Fix in rows(): a row that ends by a signal records no result (as HELD), so the next gate of the key runs it again, and the start counter (three ends without a result) raises it once if it keeps dying; drop the kept 143 at hunter-feat-pr's key. 50f99a88 fixes one source of the kill (the slice stop race); this fixes what a kill leaves behind.

Also (filed): A head's own crash (rc 139) must not count as a host fault
Monitor sweep 54 P2-b: ded32dca6 counts any row rc > 128 as held, so a head's own JVM segfault (139) shows as the three-ends alert instead of 'gate failed: dev'. Acceptance: only a signal the harness sent (the pass's or a slice stop's, read from its stop record) makes a row held; any other end is the row's result.
