---
slug: harness-orchestrator-never-blocks
track: harness
title: The orchestrator never blocks the loop on a question
kind: change
priority: P0
deps: []
created: '2026-11-01T22:49:27Z'
---
Monitor sweep 6: at 22:13:16Z the orchestrator called AskUserQuestion (whether eaglepurerocketgrape's comments file changes) and waited until 22:33:57Z; meanwhile nothing was spawned and no hand-back handled (1 of 6 slots in use 22:21:52-22:31; five listed runs waited 14-22 min; card-comment-names-commits-3 ended 'no longer due' unstarted). Root cause against R2: the orchestrator is the only spawner, so any blocking call stops the flow. Acceptance: orchestrator.md: a question to the user is asked as text in the reply (or recorded with hd ask on the change it concerns) and the loop continues; the blocking question tool is never used while runs are listed or alive; the user's answer is recorded when it comes (hd answer).
