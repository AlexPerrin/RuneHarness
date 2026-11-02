---
slug: harness-carry-gh-pr-edit-classic-projects
track: harness
title: the carry's gh pr edit fails on the Projects (classic) deprecation error; a
  failed carry records no result
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T02:11:41Z'
---
state/server-cache-clientscript-name-hash/ship.log (the user's approval of 8c6d9679e, PR 448): 'carry failed: gh pr edit failed: GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience ... (repository.pullRequest.projectCards)'. gh pr edit queries projectCards, which GitHub now errors on; edit PR fields through the REST API (gh api -X PATCH repos/<o>/<r>/pulls/<n>) instead. The same ship also logged 'carry failed: CI failure at 8c6d9679e: build & boot https://github.com/OpenRune/OpenRune-Server/actions/runs/41375908983/job/125055973126: the PR stays as it is' (the fork gate's CI had passed). hd alerted 'ship died twice without a result' (02:1xZ): each carry failure must record its result (the CI failure routes to the change, the gh fault to this change).
