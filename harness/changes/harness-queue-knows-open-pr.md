---
slug: harness-queue-knows-open-pr
track: harness
title: A queue PR for a change whose branch already has an open upstream PR updates
  that PR, never opens a second
kind: change
priority: P0
deps: []
created: '2026-11-01T20:00:07Z'
---
After harness-public-queue-on-fork shipped (2026-11-01), queue PR AlexPerrin/OpenRune-Server#36 for quest-cooksassistant at 1d586b49f says 'Opens a draft PR on OpenRune/OpenRune-Server from branch content/quest-cooksassistant', yet upstream PR 445 from that branch is already open (shipped earlier today, head 1d586b49f, ready). The rework removed ship.json and the owner:branch lookup, and the change's definition has no pr field, so the queue planned a new PR; approving would try to open a duplicate. Acceptance: the pass finds an open upstream PR by its head branch (gh pr list --head <branch> without owner, then filter by the fork owner) and records its number on the change; the queue PR then says 'Updates upstream PR N' and the carry updates it; a change whose upstream PR is already at the head, ready and commented gets no queue PR at all; a test covers both. The orchestrator asked the user to close #36.
