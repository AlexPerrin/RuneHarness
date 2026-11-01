---
slug: harness-base-move-keeps-runs
track: harness
title: A run is never ended because v8 moved under its change
kind: change
priority: P0
deps: [harness-pass-lock-short]
created: '2026-11-01T21:37:25Z'
closed: 'answer-1: misdiagnosed; superseded by harness-pass-lock-short! python3 /home/alex/osrs-harness/hd.py close harness-base-move-keeps-runs misdiagnosed; superseded by harness-pass-lock-short'
---
Observed 2026-11-01 21:34:41Z: harness-e2e-test-flaky-1, harness-limits-are-bugs-root-cause-1 and harness-gate-tools-own-files-1 were ended 'no longer due' while their agents kept working (the orchestrator then stopped the orphaned agents and the next pass listed -2 runs). At that pass their step string changed from 'dev run due' to 'dev run due: head 1f100fda7 not handed over': a harness change with no commit of its own reads its head as v8's tip, so every v8 commit (a definition commit by the orchestrator, or another change shipping) changes the run's input and ends it. Root cause: a run's input is keyed on a head that moves without the change moving. Acceptance: a run's input is the change's own facts (its definition, its own commits, its contract/answers); v8 moving (definitions or other ships) never ends a running run; a running run sees the new base at its next rebase, as today; a test commits an unrelated definition while a harness dev run is alive and checks the run is kept.

Orchestrator (2026-11-01): misdiagnosed; the monitor found the root cause (the pass holds the state lock across slow reads, so hooks are cancelled). Superseded by harness-pass-lock-short; parked behind it for the user to close.
