---
slug: harness-build-key-tools-files
track: harness
title: Builds and gates are keyed by the tools files they run, not the tools branch
  tip
kind: change
priority: P1
deps: []
created: '2026-11-01T21:17:41Z'
---
Found by the read-only monitor sweep (2026-11-01 ~21:12Z) the user asked for. cannon-review-354 rebuilt the same T d4e3edca1 39 times 00:29-14:18Z, each with a new tools-tip suffix (state/cannon-review-354/build-d4e3edca1...-<tip>.log); genie-review-355 has ~45 such logs for 69fca5fb9; each re-gate also runs fork CI. Every tools commit re-gates every gated server change. Acceptance: the build and gate key uses a hash of the tools files the build and gate execute; an unrelated tools commit re-gates nothing; a test covers a tools commit outside those files.
