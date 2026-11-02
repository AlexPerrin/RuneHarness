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

Also (filed): Contracts that already hold duplicate answer ids are renumbered, not refused
harness-contract-unique-answer-ids-1 (91be0cf) refuses a duplicate row id on parse but leaves the live duplicate in evidence/goblin-367-rsprox-dump/contract.md (two answer-2 rows, lines 58 and 60): once it ships, #367's hand-over and gate fail on a row no run wrote wrong. The change must renumber the existing duplicate (the 03:55 finding row to the next free id, its verdict rows with it) or migrate every live contract as it ships. Evidence: evidence/harness-contract-unique-answer-ids/

Also (filed): A renumbered answer row is not a new answer: it reopens nothing
Renumbering goblin-367-rsprox-dump's duplicate answer-2 (finding IC_kwDOQBbPT88AAAABeeLlXg, answered by dev run 11's head 08a6cc657) to answer-7 made hd read 'a filing or finding joined after the hand-over (answer-7)' (events.jsonl:10100, 15:33:29Z): qa run goblin-367-rsprox-dump-12 was ended mid-review (up exit 144, no verdict) and dev run 13 listed for a row already addressed. 'Joined after the hand-over' must come from the row's own time (its stamp, 03:55:58Z, before the 11 hand-over), not its id. Evidence: evidence/goblin-367-rsprox-dump/contract.md:60, evidence/goblin-367-rsprox-dump/handoff.md
