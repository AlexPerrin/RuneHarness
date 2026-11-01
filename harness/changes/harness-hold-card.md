---
slug: harness-hold-card
track: harness
title: A user's no or hold keeps a card hidden at its head
kind: change
priority: P1
deps: []
created: '2026-11-01T21:17:43Z'
---
Found by the read-only monitor sweep (2026-11-01 ~21:12Z) the user asked for. harness-review-in-console acceptance 3 asked that a 'no' leave the card hidden at that head; hd.py has no hide code. central-token-login-op's card shows in full on every pass though the user held it ('wait for other auth changes to land before considering upstream', commit 7086430), so the user is re-asked and could approve an outdated text; server-token-auth's card will do the same. state/genie-review-355/decline.json is an unread leftover of the removed hd decline. Acceptance: 'hd hold <slug> [<why>]' (the user's no or their word, recorded by the orchestrator) writes held: <head|all> to the definition; while held, the change's step is 'held by the user' (actor wait), no card; a new head or the user's lift clears it; stale decline.json files are removed; a test covers hold, new head, lift.
