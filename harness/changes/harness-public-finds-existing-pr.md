---
slug: harness-public-finds-existing-pr
track: harness
title: hd-public upstream finds the change's existing PR
kind: change
priority: P0
deps: []
created: '2026-11-01T18:12:59Z'
---
cannon-review-354's approved ship died twice without a result (state/cannon-review-354/ship.log, proc-ship.json attempts 2):

    pushed 7a8b2331a to fork content/cannon
    pr create failed: a pull request for branch "AlexPerrin:content/cannon" into branch "main" already exists:
    https://github.com/OpenRune/OpenRune-Server/pull/354

Root cause (hd-public upstream): `gh pr list -R <up> --head <owner>:<branch>` returns [] because gh's --head filter matches the head branch name only, never owner:branch. Observed:

    gh pr list -R OpenRune/OpenRune-Server --head AlexPerrin:content/cannon --state open --json number  -> []
    gh pr list -R OpenRune/OpenRune-Server --head content/cannon --state open --json number,headRepositoryOwner -> [{"number":354, "headRepositoryOwner":{"login":"AlexPerrin"}}]

So every update to an existing PR falls through to `gh pr create` and dies. Acceptance: upstream uses the change's `pr:` when set, else lists by `--head <branch>` and keeps the PR whose headRepositoryOwner.login is the fork owner; only then creates a draft. The R test covers: an existing PR on the fork branch is found and no create is attempted. After it ships, cannon-review-354's approved ship (head 7a8b2331a) reruns.
