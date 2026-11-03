---
slug: harness-ship-silent-hang
track: harness
title: A ship reports each step as it goes and never waits silently
kind: change
priority: P0
deps: []
created: '2026-11-01T18:55:59Z'
---
Observed 2026-11-01 by the orchestrator after the user's approvals of goblin-diplomacy-review-367-fftgsrq (019e5a1c4) and quest-cooksassistant (1d586b49f): 'hd-public upstream <slug> <head>' runs (pids 630339 since ~18:46Z and 641141) with no child process, ship.log empty (0 bytes) for both, and no fork CI run on either branch, so nothing was pushed after 10+ minutes. The changes show 'shipping upstream' with no fact of progress. First run of hd-public after harness-ship-records-result (PR lookup moved before the push) and harness-dependent-joins-pr (PUBLIC_BRANCH/PR env fallback). Acceptance: hd-public writes a ship.log line before and after each step (PR lookup, push, CI wait with the run it waits on, comment, ready, review request); a wait names the fact it waits for and ends on that fact or on a failure; a test runs upstream against fakes and checks each step logs; the cause of this hang is found and fixed, and both approved ships complete.
