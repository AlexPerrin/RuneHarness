---
slug: h-snapshot-defs-leak
track: harness
priority: P2
---
# test_decide snapshot plan leaks the committed harness/changes definitions



## alert 5 fault 14 (×1, first 2026-11-03T04:37:12+00:00)
tests criterion fails at base 41a9c3f, untouched by h-v9-state-root: test_decide Snapshots.test_plan_over_each_recorded_ledger plans h-criterion-cmd-dest, h-desktop-login-401, h-measure-desktop, h-measure-scope, server-training-bow absent from the recorded .plan (the committed harness/changes definitions leak into the snapshot; the live checkout has uncommitted tests/fixtures/defs-1 for it)
