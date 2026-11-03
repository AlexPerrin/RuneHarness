---
slug: harness-track-log-slug
track: harness
title: 'track.sh log PATTERN takes the pattern as the slug: empty reads and stray
  state dirs'
kind: change
priority: P1
deps: []
created: '2026-11-01T00:27:53Z'
---
The server script's header (fork local/harness tools/track.sh:11) documents `log PATTERN`, but line 14 parses `verb=$1; slug=${2:-}; arg=${3:-}`, and line 18 runs `mkdir -p state/$slug` before any check. `track.sh log "<text>"` therefore reads `docker logs server-<text>`, a container that does not exist. With `|| true` the agent gets an empty answer it takes as "not in the log", and a junk state dir is left behind.
Evidence: empty dirs in state/ named after search strings: "Have a nice day", "so you are there" (19:37), "x" (19:43), "Changes will take effect", "temporarily banned", UPDATE_FRIENDCHAT_CHANNEL_FULL_V2 (19:51), REBUILD_WORLDENTITY, WORLDENTITY (20:02), all on 2026-10-31. The client script (client/harness-v8 tools/track.sh:88) has the same shape.
Fix: document `log <slug> PATTERN` in both headers. In both scripts, refuse a slug that names no change, goal or `live` before the mkdir. One test per requirement touched. Remove the stray dirs.
