---
slug: harness-track-carries-tools-branches
track: harness
title: A harness change cannot carry a fix to a product repo's tools branch
kind: change
priority: P0
deps: []
created: '2026-10-31T23:56:28Z'
---
The track scripts live on the fork's local/harness (worktree ~/src/OpenRune-Server/.worktrees/harness) and the client's client/harness-v8. A harness change's dev ref and contract cover only osrs-harness, so a fix to tools/server/* or tools/track.sh has no ref to hand over or gate. Seen three times on 2026-10-31: harness-subject-row-range-1 asked to commit its patch on local/harness; harness-build-volume-perms-1 made local commit 256581252 there and handed over only a docs line (its track.sh build said fatal: invalid reference); harness-jav-config-local-only needs the same. A harness change must name and carry commits on the tools branches it touches, with their tests (tools/server/test_tools.py) run at the gate, and land them as a fast-forward of that branch. One test per requirement touched.
