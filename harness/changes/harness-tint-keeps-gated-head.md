---
slug: harness-tint-keeps-gated-head
track: harness
title: A base or dependency move takes no content off the live server
kind: change
priority: P1
mechanism: tree
deps: []
created: '2026-11-02T18:25:40Z'
---
Sweep 67 P3-b: T_int admits a head only while gated at its current T; gated(kept=True) (hd.py:1212-1226) covers only a tools-key move, so when the base or a dep head moves every included change leaves T_int until its re-gate, and live is deployed without it then with it (server-token-auth: the -c0485930ffdf3 suffix flips in state/live/ship.log 232-325; re-gate 16:35-16:45Z, events.jsonl 10385-10446). Against docs/ARCHITECTURE.md:172. Keep the last gated head in T_int until its re-gate replaces it. Evidence: evidence/monitor/sweep-67.md
