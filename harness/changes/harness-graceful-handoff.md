---
slug: harness-graceful-handoff
track: harness
title: Runs hand off gracefully before their context window runs out
kind: change
priority: P0
deps: []
created: '2026-11-01T11:34:23Z'
---
The user's word (2026-11-01): "handoff agents near their context window gracefully". Today the PostToolUse hook tells a run once at cfg.context_limit (150000 tokens) to hand off; runs keep reporting 'I hit the context limit partway' with work uncommitted, a subagent orphaned, a server or desktop still up, or a verdict one command away (quest-runemysteries-2..5, quest-restlessghost-5, -9, goblin-diplomacy-review-367-fftgsrq-5, server-friends-chat-clan-channels-9, -10, -17, quest-childrenofthesun-1, -3, hunter-feat-pr-5, quest-ernestthechicken-2, -3). Expected: the run is told early enough to finish cleanly (a threshold that leaves room for the hand-off: record what is judged so far as a partial verdict or hand-off rows, commit and push work in progress, stop its subagents, track.sh down, write handoff.md), and the told run stops starting new work. Measure from the runs' transcripts how much context a clean hand-off takes and set the threshold from that fact. One test per requirement touched.
