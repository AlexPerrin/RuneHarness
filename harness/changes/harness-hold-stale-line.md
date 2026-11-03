---
slug: harness-hold-stale-line
track: harness
mechanism: carry
title: 'A held: line whose head no longer matches is removed when the head moves'
kind: change
priority: P1
deps: []
created: '2026-11-01T22:09:07Z'
---
Fix-first answer to harness-hold-card at 21:32:30Z, lost (harness answers were unread note rows); hold-card shipped done at 21:52:50Z leaving a stale held: line in a definition after its head moves. Acceptance: the pass (or hd hold) removes a held: <head> whose head is no longer the change's head; a test covers it.
