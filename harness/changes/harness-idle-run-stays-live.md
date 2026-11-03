---
slug: harness-idle-run-stays-live
track: harness
title: A run idle without its hand-back stays live; an answered ask is not its record
kind: change
priority: P1
deps: []
created: '2026-11-01T02:18:26Z'
---
hook.end_run ends a run on every SubagentStop, and bind() reopens it only when the agent is resumed. Between the idle stop and the resume the pass sees no live run and lists a second run on the same change. produced() also counts an ask older than its answer as the record, so the idle stop of a run resumed after an answer ends with record true though nothing new was produced.
Evidence (state/events.jsonl, state/runs/harness-device-egress-ip-*.json):
- harness-device-egress-ip-1: ask 02:10:12Z, answer 02:12:09Z, resumed 02:12:13Z, then ended/resumed five times (ended 02:13:28, 02:14:10, 02:14:58, 02:15:43, 02:16:46; resumed 02:14:05, 02:14:53, 02:15:24, 02:16:23), each ended with record true from the pre-answer ask; its last line is 'Host ports reach, public does not. Waiting for up to finish before the Chrome check' (mid-work, no hand-back, no handover).
- harness-device-egress-ip-2 listed 02:14:30Z (step 'dev run due: head ee44c03a0 not handed over') while -1 was still working; hd now prints 'spawn: harness-device-egress-ip-2', a second dev on the same worktree.
A run ends on its SubagentHandback (or the TaskStop/gone-agent path); an idle stop records usage and last line but leaves the run live. A record must be newer than the run's last answer. One test per requirement touched.
