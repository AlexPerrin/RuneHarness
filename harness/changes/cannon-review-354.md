---
slug: cannon-review-354
pr: 354
finding:
- 4345861694
track: server
kind: change
title: 'Cannon #354: address maintainer review'
priority: P1
created: '2026-10-24T19:31:52Z'
branch: content/cannon
network: true
quest-mode: assume-completed
deps:
- cannon-354-reset-ammo-varp
- harness-subject-row-range
- harness-dupe-tests-row-scope
- harness-build-volume-perms
- harness-server-build-tree
- harness-no-powershell
- harness-server-build-musicrepository
- harness-desktop-first-login
- harness-public-finds-existing-pr
---
## Change
Upstream #354 is CHANGES_REQUESTED (Mark7625 2026-10-22 07:57, eaglepurerocketgrape 11:42). Head content/cannon 9c08b42ca. Supersedes the BR-C1 fold decision on `cannon`: the fix goes on the PR head itself.

## Definition of done
- [x] Mark7625 inline: replace the `while` loop in DwarfMulticannon.kt (no while functions)
- [x] eaglepurerocketgrape P1: replaceLostCannon (Nulodion.kt 235-250) returns only the parts matching the saved assembly stage (varp.dropcannon), not CANNON_SET.take(4); test reclaim after partial assembly and after a full cannon
- [x] fork CI green; update pushed onto the #354 head content/cannon as a merge/new commit, no force-push, after the user's OK
- [x] reply on #354 listing each fix (after the user's OK)

## Answers
- 2026-10-25T14:15:59Z console 2026-10-25: fin/grand-exchange renumbered to varp 65471 (1bea6ee22) and back in integration (tools 85bb07ab4)
- 2026-10-25T23:28:06Z The user, 2026-10-25: include it. Match every recorded fact exactly (RSProx recordings, the cache, the wiki); for a rule with no official data at all, implement the best reconstruction (LostCity's tables, or the map) and name it in the PR notes as unsourced, not in docs/quirks.md; then tick Matches the OSRS wiki, since nothing known differs. Research: evidence/area-bounds-research/ (Fossil Island underwater = regions 15008 and 15264 plane 1 from recording 3299; Mogre Camp region 11924 plane 1; Kalphite Queen destroys a cannon by a roll per shot, recording 1511; one cannon refusal tile in recording 4031).
- 2026-10-26T02:20:49Z console: the integrator's resolution is on the tools branch: local/integration-tools b7d091388 pins dev/genie-review-355 at 1c7efe27e (random_event_due 65468); the train reruns on it
- 2026-10-31T01:34:39Z The user: allow it. The guard now lets a forced push of dev/cannon-review-354 through when the new head keeps the live tip's tree (a message reword). Force-push 7a8b2331a and hand over.
- 2026-10-31T01:37:15Z console: the guard's reword check was broken (fixed in 88a6355's follow-up); the force-push of 7a8b2331a to dev/cannon-review-354 now passes the guard. Push it and hand over.
- 2026-10-31T03:59:09Z console: the dev fixed both findings in the texts at the same head 7a8b2331a (Nulodion worded as a LostCity reconstruction; quest refusal run in game, ingame/37; not-run lists replaced). Review the texts again at this head.

The user's word (2026-11-01): "Skip cannon-review-354 upstream contribute, until the third comment work is complete." The ship waits on cannon-354-reset-ammo-varp (the reply to finding 4433251631).
