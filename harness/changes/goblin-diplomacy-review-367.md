---
slug: goblin-diplomacy-review-367
track: server
kind: change
title: 'Goblin Diplomacy #367: atomic armour hand-in'
priority: P0
created: '2026-10-24T19:31:52Z'
branch: content/goblin-diplomacy
network: true
deps: [harness-close-done]
---
## Change
Upstream #367 review P2 (eaglepurerocketgrape 2026-10-22 11:42). Head content/goblin-diplomacy d77ac2b76, mergeable. Replaces the open work in `goblin-diplomacy-unstacked` for #367.

## Definition of done
- [x] handIn (GoblinDiplomacy.kt ~513-525): consuming the armour and committing quest progress/reward cannot be split by dialogue cancellation (orange, blue, brown), as #366 does for wool; completion failure does not lose the armour
- [x] test: walk away on each dialogue page of the hand-in keeps the armour or the progress, never one without the other
- [x] fork CI green; pushed onto the #367 head content/goblin-diplomacy after the user's OK
