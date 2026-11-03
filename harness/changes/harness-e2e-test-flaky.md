---
slug: harness-e2e-test-flaky
track: harness
title: EndToEnd.test_harness_change_defined_to_live never fails at random
kind: change
priority: P1
deps: []
created: '2026-11-01T21:25:07Z'
---
harness-maintainer-replies-surfaced-1 saw EndToEnd.test_harness_change_defined_to_live fail once in a full suite run, then pass alone and in two more full runs. A flaky test hides real failures at the gate. Acceptance: the cause (shared state, timing or order) is found and removed; the test passes 20 full-suite runs in a row; no sleep or retry added.
