---
slug: harness-ask-settle-baseline
track: harness
title: An edit settles any open ask, legacy ones included, and only the user's kind/deps/pr
  edits count
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T20:45:24Z'
---
Sweep 83 P2-a: asked() (hd.py:787-790) treats an ask.json with no def key as open forever (q.get('def','') in ('', settled(ch))); every ask before 8242da4 has no def, including all three open ones (server-448-cickwdoqbbpt88aaaabijnvha, server-token-refusal-logged, server-world-entity-login-tick). login-tick asked at 20:14:13Z (events.jsonl:11166) for kind local with deps [server-world-entities]; 62dfca5 (20:15:13Z) made exactly that edit, yet it is still 'question open' with its | upstream rows (contract.md:7,8,12,17,18): nxt returns at the question (hd.py:1654) before the drop (:1663). Give legacy asks a baseline (backfill def once, or the definition at ask.json's ts). P3-a: settled() (hd.py:781-784) hashes every front-matter key but finding, so harness writes settle a question without the user: cmd_new's deps rewrite (hd.py:3524-3529) and cmd_hold's held (:3397-3401); docs/PRD.md:260 names only kind, deps, pr: hash only those. Evidence: evidence/monitor/sweep-83.md
