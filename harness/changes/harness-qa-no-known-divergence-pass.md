---
slug: harness-qa-no-known-divergence-pass
track: harness
title: A qa verdict cannot pass a known divergence or an unchecked row
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T20:14:42Z'
---
Sweep 79 P2-a, case server-world-entities-16 PASS at bfb9d9853 (events.jsonl:11095): (1) qa14's failing verdict (state/server-world-entities/verdicts.jsonl, events.jsonl:10071) prescribed keying the add on MAP_BUILD_COMPLETE, contradicting RSProx 944 which it cited; (2) qa16 passed on the dev's accuracy.md 'Differences ... test-only, accepted' list (evidence/server-world-entities/accuracy.md:39-41) though ## Answers (2026-10-31) accepts only the static test raft, and no rule exempts kind: local (server tools/track.md:25,114; .claude/skills/accuracy/SKILL.md step 3); the accuracy row's 'or is a fixed difference' (track.md:133) reads as settled; (3) qa16's caveat reached the orchestrator as prose beside PASS: hook.py:224-238 enforces the one recorded line only for dev hand-overs; (4) qa16 marked a4-rebuild pass while saying it was not checked ({r: 'pass' for r in rows}, evidence/server-world-entities/qa16-rows.json) against qa.md's not-judged rule. Fix: a qa hand-back is its recorded verdict line only; any accuracy.md difference no ## Answers entry names fails the accuracy row; drop 'or is a fixed difference'; a verdict note's remedy must agree with its cited source. Evidence: evidence/monitor/sweep-79.md
