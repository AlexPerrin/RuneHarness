---
slug: harness-spotless-row-complete
track: harness
title: 'Finish harness-spotless-check-row: the verb creates its gradle volume, agreed
  contracts get the row, proven against real gradle'
kind: change
priority: P1
deps: [harness-test-no-recursive-gate]
created: '2026-11-01T22:09:06Z'
---
The user's rule (a change fixes its own limits) was sent as a fix-first answer at 21:32:16Z after harness-spotless-check-row's handover; harness answers were note rows nobody read, so it shipped done at 22:03:57Z without it (tools branch 2daf8959b). Acceptance: the spotless verb creates or reuses the slug's gradle volume itself (works on a slug never built); already-agreed server contracts get the spotless row (seed rows read at handover/gate, not frozen at contract time); the verb ran once against real gradle on a real head, log kept as evidence.

Orchestrator (2026-11-01 22:50Z): run -1 left an uncommitted hd.py edit in its worktree that added seed rows to contracts at read time and made a test gate recurse (~230 processes); waits on harness-test-no-recursive-gate. The next run must not run the full suite itself, only the touched tests.
