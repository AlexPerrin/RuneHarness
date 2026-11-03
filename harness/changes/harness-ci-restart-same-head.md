---
slug: harness-ci-restart-same-head
track: harness
title: A CI failure outside the head, with main unmoved, leaves no way to start CI
  again at the head
kind: change
priority: P1
mechanism: carry
limit-of:
- server-cache-clientscript-name-hash
- harness-split-pr-waits-dep-merge
deps: []
created: '2026-11-02T07:53:42Z'
---
server-cache-clientscript-name-hash (#448) head 8c6d9679e: upstream CI run 41375908983 failed in 'Generate cache and gameval sources' because the openrs2 cache download (FreshCache, id 2752) left no .data/cache/LIVE/main_file_cache.dat2 (the actions cache key game-cache-v2-03bcedaa... missed at 02:06Z; the same key hit at 07:20Z for content/cannon and content/quest-cooksassistant, which passed). The step reads no code of the head (FreshCache download, RemoveBzip, PackGameVals; the head adds NameCs2Groups to PluginPacks only) and fork CI at T was green. hd (next(), handover) says 'commit a fix, or rebase onto main', but origin/main is still d30985ba3, the head's base: a rebase is the same sha, and a commit with no change is not a fix. So the change can never leave this state until main moves. The account cannot re-run upstream runs, but as the PR's author it can close and reopen it, and the workflow's pull_request trigger (default types opened, synchronize, reopened) then starts CI at the same head. Acceptance: a CI failure the dev vouches outside the head reaches a fresh CI run at the same head by an act the account can do (shown on the card), and the change is not stuck while main is unmoved.

Also (harness-split-pr-waits-dep-merge): Upstream 'merged' is read from the PR's merged state, not main containing the head
harness-split-pr-waits-dep-merge-1 (8cd72b4) reports: 'merged' still means upstream main contains the dependency's head; a squash or rebase merge upstream leaves main without that head, so a split dependent's card (e.g. the clans PRs waiting on friends chat) waits forever and the 'head not rebased onto main' dev step never fires. Evidence: evidence/harness-split-pr-waits-dep-merge/notes.txt
