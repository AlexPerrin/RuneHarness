---
slug: harness-dupes-integration-tests
track: harness
title: The dupe-tests check ignores tests in src/integration/
kind: change
priority: P0
deps: []
created: '2026-11-01T00:00:49Z'
---
tools/server/text.py dupes counts only /src/test/ as a test source. The Genie's dupe tests are in src/integration/ (genie-review-355-2), so the row fails on a change that has them. Count src/integration/ too. Fix on the fork's local/harness with a test in tools/server/test_tools.py. One test per requirement touched.
