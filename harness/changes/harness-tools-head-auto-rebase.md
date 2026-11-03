---
slug: harness-tools-head-auto-rebase
track: harness
title: A carried tools head that only fell behind its live branch is rebased by the
  loop, not a dev run
kind: change
priority: P1
deps: []
created: '2026-11-01T07:05:12Z'
---
Gate failures on the tools row 'not a fast-forward of local/harness' cost a whole dev run each time another harness change shipped first: harness-up-own-keys-2, -4, harness-server-up-staff-rights-2 (and harness-server-track-test-verb-2 partly) were each spawned only to rebase a carried OpenRune-Server tools head onto a moved local/harness, with no conflict and no code change. Expected: when the only failing row is the tools fast-forward and the carried head rebases onto the live tools branch without conflict, the pass rebases it, records the new head, and re-gates; a dev run is listed only on a conflict. One test per requirement touched.
