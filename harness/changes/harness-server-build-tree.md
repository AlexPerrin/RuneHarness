---
slug: harness-server-build-tree
track: harness
title: The server build cannot configure a merged tree
kind: change
priority: P0
deps: []
created: '2026-11-01T00:00:49Z'
---
From genie-review-355-2 (tools/track.sh build, fork local/harness): (1) tree() builds its snapshot from a fresh index with add -A, which drops tracked files under ignored paths (api/generated/build.gradle.kts), so the merged tree fails to configure; read-tree HEAD into the index first. (2) The build calls :or-cache:qaCacheToolsClasspath, a task only v7's local/server-tools init script defines, and the init script is not passed. No server build has succeeded yet. One test per requirement touched; prove with one real build of genie-review-355.
