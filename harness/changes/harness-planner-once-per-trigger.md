---
slug: harness-planner-once-per-trigger
track: harness
title: The planner is listed once per trigger, not again for one it already handed
  back on
kind: change
priority: P1
deps: []
created: '2026-11-01T06:02:44Z'
---
planner-8 handed back 'nothing to file' on 'harness-server-track-test-verb [harness P2]: gate failed: dev' (the change's own failing test, back to its dev). hd then listed planner-9 with the same State line while the dev run harness-server-track-test-verb-2 was already running. The same pattern happened with the context-limit alert (planner-3..6, fixed for that trigger by harness-context-limit-alert-once). Expected: one rule for every planner trigger: a trigger a planner run has handed back on does not list the planner again until the trigger changes (a new gate T, a new alert count after that hand-back); and a gate failure whose owning dev run is live does not list the planner. One test per requirement touched.
