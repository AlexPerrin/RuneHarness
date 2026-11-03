---
slug: harness-close-symlink-worktrees
track: harness
title: close_branches removes a change's worktree whose only untracked entry is an
  ignored-by-intent symlink
kind: change
priority: P1
deps: []
created: '2026-11-01T01:49:34Z'
---
close_branches fails on three done client changes and raises an alert each pass (orchestrator-13 input):
client-api-probe-reach: cannot remove /home/alex/osrs-plugins-reverse: worktree /home/alex/osrs-plugins-reverse/.claude/worktrees/client-api-probe-reach; /home/alex/osrs-plugins-reverse: client/client-api-probe-reach not deleted
client-api-probe: cannot remove /home/alex/osrs-plugins-reverse: worktree /home/alex/osrs-plugins-reverse/.claude/worktrees/client-api-probe; /home/alex/osrs-plugins-reverse: client/client-api-probe not deleted
client-docs-no-bluestacks: cannot remove /home/alex/osrs-plugins-reverse: worktree /home/alex/osrs-plugins-reverse/.claude/worktrees/client-docs-no-bluestacks; /home/alex/osrs-plugins-reverse: client/client-docs-no-bluestacks not deleted

Facts: each of those worktrees has a clean tree except one untracked entry: `?? re`, a symlink `re -> /home/alex/osrs-plugins-reverse/re` (Oct 25). The client .gitignore has `re/`, which matches a directory but not a symlink, so `git worktree remove` (no --force for a non -build path, hd.py close_branches) refuses, the branch stays checked out and `branch -D` fails. The fix decides when a worktree holds no one's edits (e.g. the only untracked or modified entries are symlinks / ignored paths, nothing tracked modified) and removes it then; a worktree with real edits stays and is reported as now. One test in the R2 class.
