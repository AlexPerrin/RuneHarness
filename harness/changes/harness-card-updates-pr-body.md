---
slug: harness-card-updates-pr-body
track: harness
title: A card for an existing PR updates its title and body when they differ, and
  places each text where it belongs
kind: change
priority: P0
deps: []
created: '2026-11-01T20:58:57Z'
---
The genie-355-bank-lamp card (2026-11-01, head 306d7edcd, the first console card of an update with a finding) listed: push, update PR 355, CI, comment, reply in thread 4433239755, ready. It had no step to update the PR body, though evidence/genie-355-bank-lamp/pr-body.md differs from the live body (the bank behaviour the push fixes), so 355's description would stay wrong. And its texts were misplaced: the comment was only 'Updated to 306d7edcd.', while the thread reply carried the whole update comment (the push summary naming one of two pushed commits, and an unrelated ac6c6cac0 bullet). The user sent it back: "Fix first: the card must update the PR body; the comment names both pushed commits (ac6c6ca, 306d7ed) and summarises them; the thread reply answers only the line-213 finding." Acceptance: for an update of an existing PR the card shows and the carry performs 'update title/body' whenever pr-title.txt/pr-body.md differ from the live ones; the comment is pr-comment.md (the push summary naming every pushed commit), and each finding's reply is its own text (pr-reply-<finding>.md or the change's reply text), never the comment; a test covers a two-commit update with a finding: body step present, comment names both commits, reply holds only the answer.
