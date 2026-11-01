---
slug: harness-reply-only-change-posts
track: harness
title: A reply-only change on a PR posts its reply in the review thread after the
  user's yes
kind: change
priority: P1
deps: []
created: '2026-11-01T12:53:01Z'
---
Hand-back of cannon-354-reset-mcannonmulti-2 (contract agreed): per the user's answer (a), the change adds no code and its outcome is a reply to a-thoren's inline finding 4433254921 on #354 (evidence/cannon-354-reset-mcannonmulti/pr-comment.md). Two gaps: hd-public can only post a PR comment naming the head, not a reply on an inline review thread; and a change with no new commit has no step that posts it (once closed, next() returns done). The same holds for cannon-354-reset-ammo-varp and cannon-354-return-after-destroy, both reply-only by the user's answers. Acceptance: a change whose contract has no code rows reaches a card for its reply; the user's yes makes hd-public post pr-comment.md as a reply in the finding's review thread (quoting it, @ only the commenter); the change is done when that reply exists; a test covers it.
