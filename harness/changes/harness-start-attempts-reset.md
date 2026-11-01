---
slug: harness-start-attempts-reset
track: harness
title: A script's attempt count never resets, so one later death raises the died-twice
  alert
kind: change
priority: P0
deps: []
created: '2026-11-01T00:04:20Z'
---
hd.py start() (hd.py:378-393) stores attempts = previous + 1 in state/<slug>/proc-<name>.json and never resets it: not when the script writes its result, not when its args change (a new target sha). So (1) the alerts "client-api: measure died twice without a result" and "server-content: measure died twice ..." (and the six "ship died twice" alerts) stay after the scripts are fixed, until someone deletes the record by hand; (2) a measure that succeeded once on one tree raises the alert after a single death on the next tree. Evidence: state/client-api/proc-measure.json has attempts 2 with args [..., "measure", "client-api", "d34b4f08d40e..."], while the pass now measures on 71b2be488a8f. Count attempts per args (reset when args differ) and clear the record when the result lands. One test per requirement touched.
