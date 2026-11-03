---
slug: harness-maintainer-replies-surfaced
track: harness
title: A maintainer's reply in a thread we answered, a review body, or a new PR comment
  files a change
kind: change
priority: P0
deps: []
created: '2026-11-01T21:17:41Z'
---
Found by the read-only monitor sweep (2026-11-01 ~21:12Z) the user asked for. findings() skips c['reply'] and reads no review bodies or conversation comments (hd.py: 'if c["reply"] or c["bot"] ...'). After our three #354 thread replies, a-thoren's next word or a CHANGES_REQUESTED review body would never file a change, and the cannon changes stay 'waiting on the maintainers' forever. Blocks every PR's follow-up. Acceptance: a non-owner reply newer than our last reply in a thread we answered, a non-owner review with a body, and a non-owner PR conversation comment newer than our last comment each file one change on the PR (as an inline finding does, deps on the PR tip); a test covers each.
