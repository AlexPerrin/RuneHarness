---
slug: harness-main-context-limit
track: harness
title: Main hands off at the context limit too
kind: change
priority: P1
deps: []
created: '2026-11-01T03:39:53Z'
---
hook.py context_limit applies only to bound runs, so main (the head) ran past the limit and compacted, losing detail (the user: 'main compacted, should have handed off sooner'). Main holds no state beyond files, so a fresh head is cheap. Past cfg.context_limit in the main session, the PostToolUse hook tells main once to stop spawning, tell the user to start a fresh session with docs/HANDOFF.md's start prompt, and end its turn. One test per requirement touched.
