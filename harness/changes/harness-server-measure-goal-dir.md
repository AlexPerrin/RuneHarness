---
slug: harness-server-measure-goal-dir
track: harness
title: Server measure writes its report under the target sha, not the goal
kind: change
priority: P0
deps:
- harness-track-carries-tools-branches
created: '2026-11-01T00:04:13Z'
---
Alert: "server-content: measure died twice without a result (state/server-content/measure.log)". The log, twice:
FileNotFoundError: [Errno 2] No such file or directory: '/home/alex/osrs-harness/state/31241beef585f20774729063661532e245f8e310/measure.json'
hd.py measure() runs `track.sh measure <goal> <target-sha>` (hd.py:631), so in the server script (fork local/harness, ~/src/OpenRune-Server/.worktrees/harness/tools/track.sh:139) $slug is the goal and $arg the sha, but measure() writes "$root/state/$arg/measure.json", a directory that does not exist. Write to $state/measure.json (state/$slug). The fix is on the tools branch, hence the dep on harness-track-carries-tools-branches. One test per requirement touched; prove with one real measure of server-content (an empty inventory measures 0).
