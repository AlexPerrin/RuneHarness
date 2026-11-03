---
slug: harness-subject-row-range
track: harness
title: The subject seed row checks already-public commits on an existing PR
kind: change
priority: P1
deps: []
created: '2026-10-31T23:42:50Z'
---
tools/server/text.py commits checks upstream main..HEAD. On #355 that range holds the public merge 1d6c7e702 and 98c5861 (subject starts with test:), which cannot change without a force-push, so the row refuses every hand-over. The genie-review-355 qa made the row reviewer-judged after 98c5861 as a stopgap. The check should start from the PR's live head on an existing PR. The script is on the fork's local/harness branch. One test per requirement touched.
