---
slug: harness-upstream-comments-first
track: harness
title: Maintainer comments on our open PRs run before new content
kind: change
priority: P0
deps: []
created: '2026-11-01T10:13:35Z'
---
The user's word (2026-11-01): "I see we're deving new quests, but our existing PRs have upstream comments, these should be prioritized." Work: (1) read every open PR of ours on OpenRune/OpenRune-Server and OpenRune/OpenRune-Central-Server (gh, read-only) and list each maintainer comment that asks for a change; (2) for each one no change answers yet, file one change (hd new, server or central track, P0, on that PR's bucket, the comment's URL and text as evidence); (3) make the order hold: a change answering a maintainer comment is listed before any new-content change (quest-*, server-* without a PR) whatever its priority field, and a P2 change whose conflict blocks a P0 PR's test-server deploy (today server-friends-chat-clan-channels blocks cannon-review-354 and genie-review-355) is raised to its blocked change's priority. Also: the orchestrator's 'a planning request becomes a goal' does not fit a request without a measurable target (a goal without target: crashed hd in measure(), KeyError 'target'); give planning requests one place that does not crash the pass. One test per requirement touched.
