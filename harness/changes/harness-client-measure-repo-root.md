---
slug: harness-client-measure-repo-root
track: harness
title: Client track script run from its worktree takes the worktree as the repo
kind: change
priority: P0
deps:
- harness-track-carries-tools-branches
created: '2026-11-01T00:04:13Z'
---
Alert: "client-api: measure died twice without a result (state/client-api/measure.log)". The log, twice:
cp: cannot stat '/home/alex/osrs-plugins-reverse/.worktrees/harness-v8/re/host/plugins-extra': No such file or directory
Since harness-client-track-root, hd runs the client script from ~/osrs-plugins-reverse/.worktrees/harness-v8/tools/track.sh (state/client-api/proc-measure.json). The script sets repo=$(dirname "$self") (track.sh:16), so repo is that worktree, which has no re/ (the ignored inputs: re/host/plugins-extra, the re/* links that build() makes, the cmake tree); the real ones are in ~/osrs-plugins-reverse/re. Every build, up and measure from that script fails the same way, and worktrees are created under the worktree. Take the repo from CLONE (hd sets it for changes; measure gets none: hd.py:631 passes no CLONE) or from git rev-parse --git-common-dir, as the server script does with CLONE. The fix is on client/harness-v8, hence the dep on harness-track-carries-tools-branches. One test per requirement touched; prove with one real measure of client-api.
