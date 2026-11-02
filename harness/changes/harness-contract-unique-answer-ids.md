---
slug: harness-contract-unique-answer-ids
track: harness
title: 'Contract answer ids are unique: next id is the highest plus one, duplicates
  refused on parse'
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T15:18:10Z'
---
Sweep 59 P3-c: evidence/goblin-367-rsprox-dump/contract.md has two answer-2 rows (line 58, the user's dupe-tests waive 11-01T00:28; line 60, finding IC_kwDOQBbPT88AAAABeeLlXg 11-02T03:55) and no answer-1, the contract likely rewritten by a qa run; add_answer numbers by counting rows (hd.py:3069), so verdicts keyed by id collide. Evidence: evidence/monitor/sweep-59.md
