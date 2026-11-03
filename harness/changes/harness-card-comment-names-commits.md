---
slug: harness-card-comment-names-commits
track: harness
mechanism: carry
title: A card's comment always names every commit it pushes; no generic fallback
kind: change
priority: P1
deps: []
created: '2026-11-01T21:44:18Z'
---
Monitor sweep (2026-11-01): harness-card-updates-pr-body is done, but public_texts() still falls back to 'Updated to <head>.' when pr-comment.md does not name the head - the text the user rejected on the #355 card ('the comment names both pushed commits ... and summarises them') - and nothing checks that every pushed commit is named. Acceptance: an update card with pushed commits has a comment only from pr-comment.md, which must name every commit the push adds (checked against git log live-head..head); if it does not, the change goes back to its dev with that fact instead of showing a card; no generic fallback text; a test covers a stale comment after the head moves.
