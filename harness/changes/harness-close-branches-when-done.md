---
slug: harness-close-branches-when-done
track: harness
title: A change's branches and worktrees are removed when it is done
kind: change
priority: P1
deps: []
created: '2026-11-01T01:32:19Z'
---
The user's word: devs need to close their branch when done with it. Today the worktrees and branches pile up: ~/osrs-harness/.worktrees/<slug> and <slug>-build, the dev refs harness/<slug>, the carried tools branches harness/<slug> in ~/src/OpenRune-Server and ~/osrs-plugins-reverse, and their .worktrees there. When a change goes done (shipped, or live upstream) or closed, the loop removes every worktree and local branch that belongs to it, in each repo. The dev ref is the last thing removed, only after its commit is contained in the live branch or the change is closed. A dev removes any temporary worktree or branch it made that is not the change's own before it hands back. Remote branches on the fork, and anything that is public, are left alone: their removal is a public act. Sweep the existing done and closed changes once. One test per requirement touched.
