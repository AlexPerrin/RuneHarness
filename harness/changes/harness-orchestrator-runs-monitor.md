---
slug: harness-orchestrator-runs-monitor
track: harness
title: The orchestrator keeps a read-only monitor sweep running, and a new orchestrator
  session restarts it
kind: change
priority: P1
deps: []
created: '2026-11-01T21:44:44Z'
---
The user's word (2026-11-01): "Run Monitor agent continuously so we can validate changes are landing, and continue to identify harness bugs", then "Keep the monitoring running, handoff and restart minitor between sessions." (harness-monitor-on-ship was closed: not hd-listed runs, the orchestrator's own loop.) Acceptance: .claude/agents/orchestrator.md gains a step: one read-only monitor sweep is always running (a general-purpose agent, no edits, no hd pass while harness-pass-lock-short is open); when one reports, the orchestrator files its findings by the root-cause rule and starts the next, its brief naming the harness changes shipped since the last sweep and the open findings to follow up; on session start (the brief's step 1) it starts one; the last sweep's report is kept in evidence/monitor/sweep-<n>.md so the next session's sweep follows up; docs (ARCHITECTURE, the orchestrator section) state it.
