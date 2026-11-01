---
slug: harness-check-tests-full-summary
track: harness
title: The tests check row keeps too little output to read a failure
kind: change
priority: P2
deps: []
created: '2026-11-01T00:46:46Z'
---
check_tests keeps only the last 3 lines of the suite's output. Test prints that are flushed late push the Ran/OK/FAILED summary out of those lines, so a failure can't be read from the gate record (harness-jav-config-local-only-4: an earlier check-tests failure at 044cebe had no visible cause). Keep the unittest summary and the FAIL/ERROR lines. One test per requirement touched.
