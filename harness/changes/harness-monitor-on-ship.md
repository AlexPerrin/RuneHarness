---
slug: harness-monitor-on-ship
track: harness
title: A monitor run validates each shipped harness change live and sweeps for harness
  bugs
kind: change
priority: P1
deps: [harness-limits-are-bugs-root-cause]
created: '2026-11-01T21:30:23Z'
---
The user's word (2026-11-01): "Run Monitor issue continuously so we can validate changes are landing, and continue to identify harness bugs." Today the orchestrator spawned one read-only monitor sweep by hand (it found 7 issues, filed as 3e1b49c). Continuous, on observed facts, never on a timer: Acceptance: (1) each time one or more harness changes ship (their commit lands on v8 and the live hd is that commit), the pass lists one monitor run (role planner or a new monitor role, outside the agent count like the planner, read-only on product repos and GitHub); (2) its brief names the changes that shipped since the last monitor run; for each it checks the acceptance against the live state (hd output, events.jsonl, state/, GitHub read-only) and records landed / not landed with the evidence; a change not landed reopens as a change (same slug, the evidence appended); (3) it sweeps for harness bugs as the 2026-11-01 sweep did (stuck chains, repeated listings, runs without records, definitions against code, state against GitHub) and files each by the root-cause rule (harness-limits-are-bugs-root-cause: one change per mechanism, merged into an open one when it exists); (4) one monitor run at a time; it ends with its record; (5) a test covers a ship listing one monitor run and a second ship while it runs listing none.
