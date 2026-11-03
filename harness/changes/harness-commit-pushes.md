---
slug: harness-commit-pushes
track: harness
title: hd commit pushes v8 after it commits
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-02T02:26:29Z'
---
The user (2026-11-01, ET): 'Push commits to osrs-harness as changes are made.' Ships push v8, but the orchestrator's hd commit only commits: v8 was 3 commits ahead of origin/v8 (464dbaa..946e351) until pushed by hand. hd commit pushes v8 to origin after each commit, still under state/ship.lock.
