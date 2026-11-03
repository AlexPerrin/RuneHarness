---
slug: harness-close-done
track: harness
title: The loop has no way to close a change the user calls done
kind: change
priority: P0
deps: []
created: '2026-11-01T00:00:49Z'
---
The user closed goblin-diplomacy-review-367 as done (answer-1). The loop still lists qa and dev runs for it; goblin-diplomacy-review-367-2 asked again whether to retire it. A user answer must be able to close a change as done (no further runs, not in the integration tree beyond what is live), recorded and visible in hd. Then close goblin-diplomacy-review-367 and drop server-sidecar-jav-config-local-auth (refiled as harness-jav-config-local-only). One test per requirement touched.
