---
slug: harness-cards-stay-shown
track: harness
title: A card that stays due at the same head never re-wakes the orchestrator
kind: change
priority: P1
deps: []
created: '2026-11-01T13:38:53Z'
---
Observed 2026-11-01 by the orchestrator: the same four cards (cannon-review-354 7a8b2331a, genie-review-355 ac6c6cac0, goblin-diplomacy-review-367-fftgsrq 019e5a1c4, server-friends-chat-clan-channels 7fd72ec98), heads unchanged, woke state/wake.orchestrator three times in an hour; quest-cooksassistant dropped out of one pass and came back. A card absent from one pass and present in the next counts as new, so seen.orchestrator.json forgets it. Acceptance: a card re-wakes only when its head changes (or it was declined and its head moved); a pass where it is briefly absent does not reset it; a test covers drop-and-return at the same head.
