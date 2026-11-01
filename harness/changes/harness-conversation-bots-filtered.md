---
slug: harness-conversation-bots-filtered
track: harness
title: Bot comments on a PR conversation never file a change
kind: change
priority: P1
deps: []
created: '2026-11-01T21:25:06Z'
---
Limit noted by harness-maintainer-replies-surfaced-1 (b7f9122): conversation comments are read with gh pr view, which does not mark bots, so a bot's PR comment files a change like a maintainer's. Also on a PR where we never commented, every maintainer comment files a change once. Acceptance: conversation comments come from the REST issues/<n>/comments API (user.type == 'Bot' and known bot logins skipped); on a PR with no comment of ours, only comments newer than the PR's last push of ours file; a test covers both.
