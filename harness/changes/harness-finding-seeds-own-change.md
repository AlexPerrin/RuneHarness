---
slug: harness-finding-seeds-own-change
track: harness
title: A maintainer finding's change is seeded from the change it names, not the PR's
  first root
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T00:00:59Z'
---
Reported by QA run cannon-354-reset-mcannonmulti-cickwdoqbbpt88aaaabeelgiq-1: hd.py ~1506-1518 seeds a new finding change's contract and slug from roots[0], here the sibling cannon-354-reset-mcannonmulti. The new change, about eaglepurerocketgrape's P1 on Nulodion's reclaim, got that sibling's contract (a-thoren's mcannonmulti finding, its answer-1 and acc-A* rows) and a misleading slug. QA replaced the contract by hand, and the slug stays wrong. Acceptance: a finding change's slug and seed contract come from the PR and the finding itself (its thread or comment), never another change's rows; a test files two findings on one PR with two root changes and checks each one's contract and slug.
