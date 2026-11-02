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

Also (filed): track.md says at each test and dry-run line that a step is never wrapped in timeout
Sweep 64 P4-b: five harness dev runs between 15:22 and 15:36Z wrapped track.sh test, unittest or hd tick --dry-run in timeout (server-stack-one-record-2 'timeout 590', orchestrator-under-supervisor-1 'timeout 300', contract-unique-answer-ids-2 'timeout 600', handover-honours-reopen-1 'timeout 600', mobile-login-by-facts-2 'timeout 300 hd.py tick --dry-run'); hook.py:471 denied each, a turn each, though dev.md:30 forbids it. Put the rule where the command is read (tools/track.md and each product track.md test/dry-run lines), or let the hook's denial name the bare command to run. Evidence: evidence/monitor/sweep-64.md

Also (filed): hd handover prints the exact hand-back line the hook accepts
Sweep 65 P4-a: hand-backs denied for not matching the recorded hand-over line: harness-contract-unique-answer-ids-2 (15:41:03Z), harness-mobile-login-by-facts-2 (15:41:33Z), harness-handover-honours-reopen-1; a turn each. hd handover prints 'handed over <full sha> (tree ...)' (hd.py:3084) while hook.py:233 accepts only 'run <name>: handed over <sha> Limits: ...'. Have hd handover print the exact line to copy. Evidence: evidence/monitor/sweep-65.md, hook.py:223-238
