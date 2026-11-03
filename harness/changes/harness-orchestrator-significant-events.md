---
slug: harness-orchestrator-significant-events
track: harness
title: The orchestrator runs on significant events only
kind: change
priority: P1
deps: []
created: '2026-11-01T03:28:56Z'
---
The user's word: stop listing the orchestrator every 50 events; count only significant events. Today orchestrate() lists a run on any alert, a goal below target with nothing open, or 50 events since the last run. 18 runs have gone by tonight, several filing nothing. Trigger only on: a new alert, a run that ended without its record, a gate or ship failure, a script that died, or a goal below target with nothing open. Drop the event count. One test per requirement touched.
