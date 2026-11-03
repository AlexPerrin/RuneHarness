---
slug: harness-spotless-without-tcommit
track: harness
title: track.sh spotless runs at the change's head without TCOMMIT
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T16:04:38Z'
---
server-cache-clientscript-name-hash-10 (qa): 'track.sh spotless' with no TCOMMIT fails ('dev/<slug> is already used by worktree'); with T's first part it fails because that is a tree sha, not a commit; it passed only with TCOMMIT set to the head commit by hand. Evidence: evidence/server-cache-clientscript-name-hash/qa-10-rows.json
