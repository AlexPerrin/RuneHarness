---
slug: harness-tools-pinned-per-process
track: harness
title: A running build, gate or deploy runs from a pinned copy of the tools; a tools
  ship never changes files under it
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-01T22:49:27Z'
---
Monitor sweep 6, a limit of harness-gate-tools-own-files: live deploy attempt 2 (ee13b4c, started 22:09:22Z) ran the old track.sh, which builds with $self/server/Dockerfile; the tools ship at 22:27 fast-forwarded the fork's tools worktree and moved that file to tools/gate/; at 22:35:22 the deploy failed 'open Dockerfile: no such file' after 26 min of cache download; the test server is still on 7e4f3525 from 19:20; attempt 2 wrote no ship.log line. Root cause: running scripts execute from the same tools worktree a ship mutates. Acceptance: each build/gate/deploy runs from a checkout of the tools at the commit its key names (a per-key read-only worktree or archive), so a ship never mutates a running process's tools; a test ships tools while a fake deploy runs.
