---
slug: harness-late-answer-same-second
track: harness
title: late_answers orders a row and a hand-over or brief of the same wall-clock second
  by chance
kind: change
priority: P1
mechanism: contract
limit-of:
- harness-close-alert-pasteable
deps: []
created: '2026-11-02T04:46:27Z'
---
The full suite fails at random in tests that write an answer row and a hand-over or brief close together: ship-harness gate f058a0610 failed R5.test_open_question_holds_gate_and_ship_until_answered (the user's answer did not reach the dev: ('script', gate) != ('dev', [])), and a full run at harness-close-alert-pasteable failed R6.test_a_pr_round_of_n_findings_and_one_head_move_costs_one_dev_one_qa_one_gate_and_one_card (a joined finding counted late: a second dev run); both pass alone and in other full runs. late_answers (hd.py:1443-1456) compares second-resolution now() strings (row text[:20] against the hand-over ts, its given, and verdict ts), so whether a row is before or after its record depends on where a second boundary falls. Order these facts by something that cannot tie (a sequence in the contract or the record, or the row's presence in the brief), not by wall-clock seconds; no sleep or retry. Acceptance: both tests pass 20 full-suite runs in a row. Evidence: state/ship-harness/tests.txt, evidence/harness-close-alert-pasteable/.
