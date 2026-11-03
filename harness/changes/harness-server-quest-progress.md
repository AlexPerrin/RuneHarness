---
slug: harness-server-quest-progress
track: harness
title: The test server treats every quest requirement as met
kind: change
priority: P1
deps: []
created: '2026-11-01T02:21:56Z'
---
quest-cooksassistant-3: the test server runs with upstream's default game.example.yml quest requirements setting assume-completed, which skips every quest check (the Lumbridge range cooked for a player who had not started Cook's Assistant). Judging a quest's requirements needs respect-progress. Set the test server's quest requirement mode to respect-progress in the server track's up (the config the harness mounts, not the fork's tree), so every server change is judged with real quest checks. Say so in the server track's tools/track.md so PR notes can name it. Evidence: evidence/quest-cooksassistant/handoff.md. One test per requirement touched.
