---
slug: harness-up-keeps-account-state
track: harness
title: A run's server up can resume the tester account where the last run left it
kind: change
priority: P1
deps: []
created: '2026-11-01T04:36:58Z'
---
goblin-diplomacy-review-367-fftgsrq-5 hand-back (context limit before a verdict): each up wipes the account, so the next QA run has to replay the quest back to the stage its remaining rows need (completed journal, W6, W10-W12, rows 17-18, C7, C9 restart, C10). A long quest review costs one replay per run. Expected: up can start from the account state a previous run of the same change saved (or a named quest stage), so a resumed run starts where the last stopped. Accuracy rows stay judged in play, never on a seeded state that skips what they test. One test per requirement touched.
