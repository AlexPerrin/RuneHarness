---
slug: harness-fail-verdict-before-regate
track: harness
title: a FAIL verdict waits behind a re-gate of the same head
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T03:49:33Z'
---
sweep-31 P2-c: quest-cooksassistant's FAIL verdict at 667a4a843 (03:29:51Z) waited for a full re-gate under new tools before its dev step: nxt() runs the gate before the verdict at the same head, spending CI on a head already known to fail. A failed verdict at the current head gives the dev step first. evidence/monitor/sweep-31.md
