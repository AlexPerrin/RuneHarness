---
slug: harness-split-pr-waits-dep-merge
track: harness
title: A same-track dependent the user keeps as its own PR waits for its dependency's
  upstream merge
kind: change
priority: P1
mechanism: tree
limit-of:
- server-clan-channels
deps:
- harness-ci-restart-same-head
created: '2026-11-02T07:52:28Z'
---
The user's answer-3 on server-clan-channels (2026-11-02T07:48:17Z): friends chat (server-friends-chat-clan-channels) its own PR first, clans after it, one change per PR. hd cannot carry that: join() (R8) makes every upstream change with no pr or branch of its own, whose open same-track dependency goes upstream, part of that dependency's PR and waits on no upstream merge; a change given a branch of its own whose head holds the dependency's unmerged commits is 'stacked', a dev step it can never leave (clans needs friends chat's side tab code, so its head cannot drop those commits before friends chat merges). Root cause: R8 has no form for the upstream rule 'shared code is its own change that merges first; Depends: in the PR text' (track.md). Fix in the tree mechanism: a dependent marked as its own PR (its definition's branch: or a split flag the user's answer sets) is built, gated and deployed to the test server on T with its dependency as now, but its card waits until the dependency's PR is merged upstream; then a head still holding the dependency's pre-merge commits is a dev step (rebase onto main), and the stacked check is judged against main. server-clan-channels then gets its own branch (content/server-clan-channels) instead of joining content/server-friends-chat-clan-channels; its PR text already says Depends: the friends chat PR.
