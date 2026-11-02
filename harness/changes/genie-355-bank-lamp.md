---
slug: genie-355-bank-lamp
finding: 4433239755
track: server
title: '#355: Talk-to at a bank gives the lamp (GenieRandomEvent.kt:213)'
kind: change
priority: P1
pr: 355
created: '2026-10-31T23:42:50Z'
deps:
- harness-no-powershell
- genie-review-355
- harness-card-updates-pr-body
- harness-server-build-musicrepository
- harness-desktop-first-login
- harness-build-gate-keyed-process
- harness-github-reads-budget
---
a-thoren inline on #355 at 98c5861, 2026-10-31 20:47Z, GenieRandomEvent.kt line 213: Talk-to at a bank gives no lamp. Wiki: the Genie follows players into banks and does not despawn at banks (update 2023-11-01). accuracy.md 7e in evidence/genie-review-355 marks the difference.

Orchestrator (2026-11-01 23:05Z): its gate failed on CI for an external reason (GitHub quota 403 / openrs2 cache fetch), not its code; held until those fixes land so no dev run is spent on it.
