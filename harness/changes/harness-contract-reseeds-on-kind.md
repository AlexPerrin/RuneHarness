---
slug: harness-contract-reseeds-on-kind
track: harness
title: A change of kind or deps re-seeds its contract, and a definition that settles
  an ask releases it
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T20:24:49Z'
---
Sweep 80 P2-a: 62dfca5 (20:15:13Z) set server-world-entity-login-tick to kind local with deps [server-world-entities]; at 20:23Z it was still 'question open' (events.jsonl:11172): the qa's ask (state/server-world-entity-login-tick/ask.json, 20:14:13Z) clears only through hd answer (add_answer hd.py:3320-3337; next() waits hd.py:1640). Its contract (written 20:14:02Z under kind change) keeps 5 '| upstream' rows (no-deferral, net-change, one-change, subject, texts); unseeded()/add_seeds (hd.py:731-739) only add or replace seed rows, never drop ones that no longer apply. Also sweep 80 P4-b: hd new --touches is required only for kind change (reach() hd.py:3519) though docs/ARCHITECTURE.md:84 and docs/PRD.md:187 say every product track; .claude/agents/orchestrator.md:46-47 files product changes with hd new without --touches. Evidence: evidence/monitor/sweep-80.md
