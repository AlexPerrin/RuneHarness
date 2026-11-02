---
slug: harness-roles-search-roots
track: harness
title: runs search the whole filesystem from /
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T05:09:25Z'
---
sweep-38 P2-a and sweep-40 P2-a: a reader under server-clan-guest-1 ran 'find / -name *.cs2 -path *clan*' (3.5 min) and server-world-entities-10 ran 'find / -iname *rsprot*.jar' (~2.5 min, 05:06-05:08Z), both walking /mnt/c. The role files (dev, qa, reader) name the search roots (the gradle cache ~/.gradle, the clones under ~/src, ~/osrs-plugins-reverse, this repo) and forbid a search from /. evidence/monitor/sweep-40.md
