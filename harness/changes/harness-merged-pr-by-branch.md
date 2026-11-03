---
slug: harness-merged-pr-by-branch
track: harness
title: A change whose head a merged PR holds is done though it has no pr record
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T20:30:47Z'
---
quest-cooksassistant shows a card (2026-11-02 20:3xZ) to push 07f01dc9a and open a new draft PR on OpenRune/OpenRune-Server, yet gh pr view 445 says MERGED at 2026-11-02T16:34:49Z with headRefName content/quest-cooksassistant and headRefOid 07f01dc9a9cd2be4e83dc4e03765871bef825118. done() (hd.py:1150) takes the PR number only from the change's pr: or state/<slug>/opened.json; quest-cooksassistant has neither (carried before those records), and hd.py:1036-1042 finds a PR by branch only among open PRs. The merged-PR fix joined to harness-finding-needs-ask (d52ed2c) did not ship with it. Find the PR by its head branch among closed PRs too (or from state/<slug>/ship.json, which names 'upstream PR 445 at 07f01dc9a'); a change whose head a merged PR holds is done. Approving the card would open a duplicate PR. Evidence: state/quest-cooksassistant/ship.json, gh pr view 445
