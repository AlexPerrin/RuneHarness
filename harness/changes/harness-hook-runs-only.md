---
slug: harness-hook-runs-only
track: harness
title: The hook denies commands that only quote hd approve or hd close
kind: change
priority: P1
deps: []
created: '2026-11-01T00:14:54Z'
---
hook.py's PreToolUse rule matches any Bash command line containing the approve/close command text, so it denied a dev's heredoc and grep that only edited or searched files quoting it (harness-dupe-tests-row-scope-2, harness-close-main-only-1, harness-parallel-spawn-binding-1). Devs fell back to the Edit tool. Match only a command that runs hd with that verb. One test per requirement touched.
