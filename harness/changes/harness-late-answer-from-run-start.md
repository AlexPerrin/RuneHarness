---
slug: harness-late-answer-from-run-start
track: harness
title: a filing joined during a dev run counts as taken by that run's hand-over
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T01:54:07Z'
---
sweep-19 N10: late_answers (hd.py:1322-1332) keeps only rows with ts >= the hand-over ts. answer-3 on harness-gate-ci-cache-miss-cannon (N7, 01:46:35Z) was written 8 s before run -3's hand-over (01:46:43Z, Limits: none), whose brief predated it; the change went done 01:50:16Z without any N7 code. Measure lateness from the start of the run whose record it is (its 'started', as hd.py:2036-2040 does), or refuse a hand-over when an answer row is newer than the run's start. Also: the joined filing is logged as action 'limit' (merge_limit, hd.py:2838), misnaming a plain filing. evidence/monitor/sweep-19.md
