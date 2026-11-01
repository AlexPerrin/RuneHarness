---
slug: harness-handback-taskstop-ends
track: harness
title: A background command stopped with TaskStop counts as ended at the hand-back
kind: change
priority: P1
deps: []
created: '2026-11-01T11:55:57Z'
---
harness-devtools-screenshot-hang-1: a background Bash (bx1t1a2qi) stopped with TaskStop, as hook.py's hold_handback tells a run to, never produced a <task-id> notification in the run's transcript (the TaskStop result carries it as "task_id":"bx1t1a2qi"), so running() still listed it and SubagentHandback was denied with no way out. Expected: hold_handback counts a task stopped by TaskStop (its result's task_id, or a later lookup failing with No task found) as ended. One test per requirement touched (R2).
