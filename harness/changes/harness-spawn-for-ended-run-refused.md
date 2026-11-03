---
slug: harness-spawn-for-ended-run-refused
track: harness
mechanism: runs
title: An agent spawned for a run that has already ended is refused at its start
kind: change
priority: P1
deps: []
created: '2026-11-01T21:24:37Z'
---
The user's word (2026-11-01): limits noted by harness-listed-run-not-dropped-1 'become new bugs'. An agent spawned for a run the pass already ended (e.g. harness-drop-hd-user-alert-2: ended 18:31:20, started 18:31:25, record false) still runs, untracked and outside the agent count; the hook refuses nothing. Acceptance: SubagentStart (or the first PreToolUse) of an agent whose brief names an ended run stops it at once with a message to the orchestrator naming the run and the reason it ended; the run stays ended; a test covers it.
