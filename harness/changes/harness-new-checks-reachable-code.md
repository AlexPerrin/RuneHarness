---
slug: harness-new-checks-reachable-code
track: harness
title: A change filed on code that lives on another change's branch carries that dep
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T19:52:49Z'
---
Sweep 76 P3-a: harness-live-stack-issuer-2 filed server-token-refusal-logged with deps [] (events.jsonl:11030) though every line it edits (ConnectionHandler.tokenLogin, TokenLoginVerifier, AccountLoadResponseHook's token path) exists only on dev/server-token-auth; its contract qa then asked the user to add the dep (11068, state/server-token-refusal-logged/ask.json) and it holds on 'question open' for a fix the definition should have carried. hd new neither checks nor prompts that the code a change touches is reachable from main plus its deps; the filing run knows the branch. Evidence: evidence/monitor/sweep-76.md
