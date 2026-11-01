---
slug: harness-spotless-check-row
track: harness
title: hd handover refuses a head that fails spotless on any module it changes
kind: change
priority: P1
deps: []
created: '2026-11-01T21:17:41Z'
---
Found by the read-only monitor sweep (2026-11-01 ~21:12Z) the user asked for. server-npc-examine-without-overlay failed CI 'Formatting' three times (19:54:25, 20:32:55, 21:03:10Z; 202c77bd7 re-gated once unchanged) before dev run -4 fixed pre-existing lint in a file it touched (spotless ratchet). Acceptance: a check: row in the server track runs spotlessCheck over every module the head changes against main, so handover fails instead of CI; a test covers a touched file with old lint.
