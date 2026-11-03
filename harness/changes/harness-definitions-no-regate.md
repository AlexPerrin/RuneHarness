---
slug: harness-definitions-no-regate
track: harness
title: A definition commit on the live branch re-builds and re-gates every open harness
  change
kind: change
priority: P0
deps: []
created: '2026-11-01T00:12:45Z'
---
The harness base is the live branch v8 (harness-ship-onto-live-branch), and the head commits every change definition (hd new, deps edits) on v8. Each such commit moves the base, so T and its tree move for every open harness change, and the pass starts a new build and gate, with no code difference. Evidence (state/events.jsonl, git reflog v8, UTC): harness-build-volume-perms built on da21f3375 00:07:11, 16a97aab8 00:08:48, 885ff46db 00:09:12, 5234629e0 00:10:03, 2d2537d3e 00:11:50, and harness-jav-config-local-only on 3d00c7552 00:06:51, 816e9f191 00:07:11, ad2c7708d 00:08:48, d703b29cb 00:09:13, cad64cb1d 00:10:03, 7567f9612 00:11:50: six trees in five minutes. v8 moved at 00:07:10 (commit 'harness: change harness-tools-no-pycache', harness/ only), 00:09:09 ('harness: change harness-close-main-only', harness/ only), 00:12:00 ('server changes wait on harness-server-build-tree', harness/ only), between ships at 00:07:34, 00:09:53, 00:11:19. Both changes' last builds succeeded (state/<slug>/build.json ok true, detail 'build copy ... at <the proc-build TCOMMIT>') on a tree already stale, and the died-twice alert followed (that false alert is harness-start-attempts-reset's; this change is the churn behind it). Ship meanwhile refuses each time v8 moved past the gated base. Fix so that a commit touching only harness/ (definitions) does not change what is built, gated or shipped: for example key the build and gate on the tree without harness/, or keep definitions off the gated tree. A real code move on v8 still re-gates. One test per requirement touched.
