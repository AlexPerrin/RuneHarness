---
slug: harness-answer-quotes-question
track: harness
title: An answer row quotes the question it closes
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T21:16:07Z'
---
Sweep 85 P2-a: add_answer writes 'the user: <text>' and drops ask.json, so the question is gone: the dev sees only 'answer-1 | 2026-11-02T20:59:29Z the user: a' (evidence/server-token-refusal-logged/contract.md:29; server-448 contract.md:24 the same). For server-token-refusal-logged (a) meant 'add deps [server-token-auth]' (events.jsonl:11068 truncates the question); nobody applied it, run -2 built 139f119d6 without the dep, the build broke and it filed harness-tree-transitive-central (11458-11459). The answer row quotes the ask it closes (and the orchestrator applies a definition edit the answer names). Evidence: evidence/monitor/sweep-85.md
