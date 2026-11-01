---
slug: genie-review-355
pr: 355
track: server
kind: change
title: 'Genie #355: address maintainer review and our gate findings'
priority: P0
created: '2026-10-24T19:31:52Z'
branch: content/genie
network: true
deps: [harness-dupes-integration-tests, harness-server-build-tree, harness-gate-ci-slug, harness-no-powershell]
---
## Change
Upstream #355 (draft) has two review findings from eaglepurerocketgrape (2026-10-22 11:42). Head content/genie 1d9b6fa49. Folds in the pending gate findings held on `genie`.

## Definition of done
- [x] `::randomevent` registered with requiredRights = Rights.ADMINISTRATOR (or removed) (review P1)
- [x] talk(): keep Genie ownership and cleanup valid across the dialogue suspension; cancel at the open page and logout there leave no orphan Genie and still deliver the lamp (review P2)
- [x] full inventory at completion does not discard the lamp; tests for cancellation, logout and full inventory
- [x] our gate findings (fix-genie-gate-findings): leaves on the next call tick after Talk-to; lamp XP equal to its message
- [x] fork CI green; pushed onto the #355 head content/genie after the user's OK; #355 stays draft until then

## Answers
- 2026-10-25T23:28:06Z The user, 2026-10-25: include it. Match every recorded fact exactly (RSProx recordings, the cache, the wiki); for a rule with no official data at all, implement the best reconstruction (LostCity's tables, or the map) and name it in the PR notes as unsourced, not in docs/quirks.md; then tick Matches the OSRS wiki, since nothing known differs. Research: evidence/area-bounds-research/ (Fossil Island underwater = regions 15008 and 15264 plane 1 from recording 3299; Mogre Camp region 11924 plane 1; Kalphite Queen destroys a cannon by a roll per shot, recording 1511; one cannon refusal tile in recording 4031).
- 2026-10-31T03:03:18Z The user: the pass now replaces the #355 description with pr-body.md on the approved push (the card shows it, the approval binds its digest). Update pr-body.md to be true at the new head, and fix the comment's test claim (add the Genie-left check to the full-inventory test, or reword).
