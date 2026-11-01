---
slug: harness-reply-only-one-run
track: harness
title: A finding answered with no code is one QA run, as PRD R4 states
kind: change
priority: P1
deps: []
created: '2026-11-01T21:44:18Z'
---
Monitor sweep (2026-11-01): PRD R4 and the user's word on harness-public-queue-on-fork ('a reply-only change is one run') are not in the code: nxt() lists a contract QA run, then dev, then a review QA run, skipping only the gate. cannon-354-reset-mcannonmulti took 5 runs, return-after-destroy 4. Acceptance: in nxt(), a change with a finding whose answer needs no commit (the contract says so, or the QA run decides) gets one QA run that writes the contract, the reply (pr-reply-<finding>.md) with its proof, the verdict and the handover; no dev or review run is listed for it; a test covers the listing sequence.
