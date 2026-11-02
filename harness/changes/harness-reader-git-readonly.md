---
slug: harness-reader-git-readonly
track: harness
title: The reader rule allows read-only git subcommands
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T18:25:40Z'
---
Sweep 67 P3-a: hook.py:509-510 denies git (merge|stash|tag|worktree|config|...)\b for a reader; \b matches before '-', so read-only git merge-base and merge-tree are denied, as are git stash list, git worktree list, git tag --contains, git config --get. Reader of hunter-feat-pr qa denied 'git merge-base 049a26312 3aeff1610' at 18:05:41Z and 18:05:45Z (state/events.jsonl). Match whole subcommands and allow their read-only forms. Evidence: evidence/monitor/sweep-67.md
