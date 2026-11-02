---
slug: harness-mechanism-alert-ordered-split
track: harness
title: the one-open-change-per-mechanism alert cannot accept two changes a dependency
  orders
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T01:55:04Z'
---
planner-20 hand-back: the user wanted a run's idle-logout fix unblocked (split as P0 harness-run-idle-logout-off with harness-server-stack-deploy depending on it); hd's alert 'mechanism server: 2 open changes ...: merge them' forced a merge, and a change waits on all its deps, so the merged harness-server-stack-one-deploy holds the P0 idle-logout fix behind server-token-auth. The alert rule (R3 in hd.py _pass) must accept two changes on one mechanism when a dependency orders them.
