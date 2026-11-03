---
slug: harness-alert-names-failure
track: harness
title: The live 'ended without a result' alert quotes the failure it ended on
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T18:07:16Z'
---
Sweep 66 P5: the alert 'live: ship ended 3 times without a result' (hd.py:1328) hides the failure line state/live/ship.log names ('failed: ... (exit 1)' and the docker error 'not a directory'); the user and orchestrator must open the log to learn it. Quote the last failure line in the alert. Evidence: state/live/ship.log, evidence/monitor/sweep-66.md
