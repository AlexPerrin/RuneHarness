---
slug: harness-dupes-from-live-head
track: harness
title: text.py dupes checks only what follows an existing PR's live head
kind: change
priority: P0
deps: []
created: '2026-11-01T12:57:20Z'
---
tools/server/text.py dupes diffs $BASE...$HEAD, while commits scopes to the commits after fork/$PUBLIC_BRANCH when $PR is set. On cannon-354-reset-mcannonmulti the dev ref is #354's live head 7a8b2331a (no new commit, the user's answer-1), yet dupe-tests fails on the whole PR's item flows in dwarven-mine and dwarf-multicannon. Fix: on an existing PR, diff fork/$PUBLIC_BRANCH...$HEAD (an empty diff passes), as commits does. One test for the row's scope.
