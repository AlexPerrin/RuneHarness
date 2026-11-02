---
slug: harness-contract-rows-migrate
track: harness
title: A changed seeded contract row reaches every open contract, not only missing
  ids
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T15:40:47Z'
---
Sweep 62 P3-c: 556165f seeds the harness tests row as a hand-over check (tools/track.md:16), but all 290 harness contracts, the open ones included (contract-unique-answer-ids, gate-held-row-own-stop, mobile-login-by-facts, live-stack-issuer, mobile-up-by-facts), still hold '- tests | ... | gate: tools/track.sh check-tests': seeding adds only missing row ids (hd.py:1573). harness-handover-honours-reopen handed over at 15:34:00Z on a 24-test targeted run, not the suite. Evidence: evidence/monitor/sweep-62.md
