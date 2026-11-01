---
slug: harness-stopped-run-ends
track: harness
title: A run the head stops never ends in the loop
kind: change
priority: P1
deps: []
created: '2026-11-01T01:26:17Z'
---
When the head stops an agent with TaskStop, no SubagentStop hook fires, so its state/runs/<name>.json keeps ended null and the run holds an agent slot for good. Seen: genie-review-355-5 (stopped 00:3xZ) and harness-jav-config-reland-1 (stopped when the user closed it) were still listed as live runs at 01:3xZ. The head ended both records by hand. The pass should end a run whose agent is gone (its transcript no longer grows and no live agent maps to it in by-agent), or the head's stop should go through hd and end the record. One test per requirement touched.
