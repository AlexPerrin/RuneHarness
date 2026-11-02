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

Also (filed): the carry's CI wait judges a failed upstream check the head's even when the failing step does not read the head
Planner-21 (alert: server-cache-clientscript-name-hash ship died twice without a result). state/server-cache-clientscript-name-hash/ship.log: 'carry failed: CI failure at 8c6d9679e: build & boot https://github.com/OpenRune/OpenRune-Server/actions/runs/41375908983/job/125055973126: the PR stays as it is'. The failed step is 'Generate cache and gameval sources' (:or-cache:freshCache): the OpenRS2 download left no cache, 'FileNotFoundException: Main file not found at .../.data/cache/LIVE/main_file_cache.dat2' (02:09:39Z); the head (a clientscript name hash) is not read by that step, and the fork gate CI at the same head passed. Root cause against PRD (a gated head is carried; only the head's defects come back as changes): carry() (hd.py:2468) raises on any non-success check, while the build-gate mechanism (harness-build-gate-keyed-process) already classifies a CI failure by whether its failing step reads the head; two classifiers of one fact. This replaces the rule in harness-carry-gh-pr-edit-classic-projects's body that 'the CI failure routes to the change': one classifier, shared by gate-ci and the carry's CI wait. Acceptance (with a test): a carry whose upstream check fails in a step that does not read the head (cache/gameval generation, checkout, setup, cancelled, timed out) records that fact as the carry's result with no FAIL and no dev step for the change, and re-runs the failed job (gh run rerun --failed) on the observed fact the source answers, never a timed retry; a failure in a step that reads the head records the change's FAIL and lists its dev step; either way the ship ends with a result, so 'ship died twice without a result' cannot arise from a CI failure.
