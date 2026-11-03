---
slug: harness-server-build-musicrepository
track: harness
title: A server build fails in MusicRepository.kt
kind: change
priority: P1
deps: []
created: '2026-11-01T01:10:05Z'
---
harness-no-powershell-2 reports this change's server build fails in MusicRepository.kt. Find whether it is the integration tree (a pin or gated head breaking the build) or the build tooling, and fix it or file the server change that does. Evidence: evidence/harness-no-powershell/proof.md (harness-no-powershell-2).
