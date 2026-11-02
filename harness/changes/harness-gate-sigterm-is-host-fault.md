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
