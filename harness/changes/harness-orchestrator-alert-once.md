---
slug: harness-orchestrator-alert-once
track: harness
title: An alert already answered does not list the orchestrator again
kind: change
priority: P1
deps: []
created: '2026-11-01T00:50:49Z'
---
Fact that repeats: the alert "client-api: measure died twice without a result (state/client-api/measure.log)" listed three orchestrator runs while open changes already remedy it. orchestrator-3 filed harness-client-measure-repo-root (fixed on client/harness-v8 7d3b32b). The log's later lines are the PowerShell refusal and "track.sh: line 52/54: powershell.exe: command not found", both remedied by harness-no-powershell (dev run harness-no-powershell-2 alive, head 044cebee6). orchestrator-4 ended with record false after 14 turns, last line "There is already a `harness-no-powershell` change with runs. Let me read it and its runs." (state/runs/orchestrator-4.json). orchestrator-5 was listed on the same input and found nothing new to file.
Two defects in one mechanism. (1) hook.py produced() counts only an `hd new` event as the orchestrator's record, so a run that correctly finds nothing to file ends record false; two such runs on the same input raise "orchestrator: 2 orchestrator runs ended without a record" to the user (hd.py dispatch, R5) though nothing failed. (2) hd.py orchestrate() lists a run for every current alert, including one an open change already answers, until that change ships and the script's result lands.
Fix with one mechanism: an orchestrator run's hand-back is its record whether it files or not (e.g. the orchestrator records the alerts it handled, via the existing record path), and orchestrate() leaves out an alert whose text a handled record or an open change already carries, so it lists the orchestrator again only when the alert text changes or the covering change closes with the alert still raised. One test per requirement touched.
