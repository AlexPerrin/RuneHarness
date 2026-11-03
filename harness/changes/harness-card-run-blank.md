---
slug: harness-card-run-blank
track: harness
title: 'A card''s verdict line names no run: ''(run )'''
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T06:31:28Z'
---
Monitor sweeps 46 and 47 P2-c: the #448 card (server-cache-clientscript-name-hash, head 8c6d9679e) prints 'verdict at 8c6d9679ee5b: 22 rows pass (run )'. Acceptance: the card names the run that recorded the verdict, or drops the parenthesis when none is recorded.
