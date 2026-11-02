---
slug: harness-card-finds-open-pr
track: harness
title: a re-carry card says 'open a draft PR' when the PR is already open
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T04:02:44Z'
---
server-cache-clientscript-name-hash's card at 8c6d9679e (~04:0xZ) lists '1. open a draft PR on OpenRune/OpenRune-Server from content/server-cache-clientscript-name-hash' although PR #448 is open (draft, head 8c6d9679e, AlexPerrin:content/server-cache-clientscript-name-hash; gh pr list --head finds it). An approved card would try to open a duplicate. The carry's PR lookup finds the open PR of the change's branch (by head owner:branch) and the card re-runs its CI and posts the comment instead.
