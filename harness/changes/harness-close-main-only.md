---
slug: harness-close-main-only
track: harness
title: Only main can close a change
kind: change
priority: P1
deps: []
created: '2026-11-01T00:09:09Z'
---
harness-close-done adds hd close <slug> <text> (the user's word). hook.py's PreToolUse rule stops a subagent from running hd approve but not hd close; closing a change is the user's decision, recorded by main, so the same rule covers hd close. Also: the dev brief still says the harness base is main, while harness-ship-onto-live-branch made it the live checkout's branch (v8); devs branch from v8 against the brief. One test per requirement touched.
