---
slug: harness-desktop-walk-to-long
track: harness
title: Desktop walk_to moves the player over long distances
kind: change
priority: P2
deps: []
created: '2026-11-01T04:52:53Z'
---
quest-restlessghost-4 hand-back: on the desktop client, short walk_to calls worked but longer walk_to clicks failed to move the player, so the dev used ::tele for travel (named in the PR body). Every quest play-through and QA review travels; a cheat for travel is a step a review must name and a reader must discount. Expected: osrs-devtools-desktop walk_to reaches a far tile (by stepping through reachable intermediate tiles or the client's own pathing) and wait_for confirms arrival. Proof: walk_to from Lumbridge to the Draynor swamp altar reaches it with no teleport. One test per requirement touched.
