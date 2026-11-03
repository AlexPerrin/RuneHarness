---
slug: harness-client-track-root
track: harness
title: hd crashes when the client track script is not at the repo root
kind: change
priority: P0
deps: []
created: '2026-10-31T23:29:03Z'
---
python3 hd.py (tick) dies with FileNotFoundError: /home/alex/osrs-plugins-reverse/tools/track.sh while measuring goal client-api (hd.py:622 measure -> start -> spawn). The client's track script lives on branch client/harness-v8, worktree ~/osrs-plugins-reverse/.worktrees/harness-v8/tools/track.sh (HANDOFF). track_root (hd.py:176) returns the repo path for the client because repos.client has no tools key, and hardcodes .worktrees/harness when it has one. Fix in the loop so the pass never crashes on a missing script (an alert, not a traceback), and resolve the client's track root correctly (hd.yaml and track_root). Also arm-the-watch note: inotifywait is not installed on this host; the head polls state/wake mtime. One test per requirement touched.
