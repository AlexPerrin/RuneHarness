---
slug: harness-fail-step-counts-fails
track: harness
title: a FAIL step counts not-judged rows as failures
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T05:56:31Z'
---
sweep-44 P2-b: hd.py:1555 builds 'failed' from every row that is not 'pass': hunter-feat-pr's step read 'FAIL 94 rows: dev' while the verdict recorded failed=4 (05:51:57Z); the detail opens with 90 not-judged lines and the event text is cut at 600 chars, so the one real defect never shows and the dev brief buries the 4 fails under 90 open rows. Count and list the fail rows; name not-judged rows apart. evidence/monitor/sweep-44.md
