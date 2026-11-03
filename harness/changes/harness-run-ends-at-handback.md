---
slug: harness-run-ends-at-handback
track: harness
title: A run ends at its hand-back, not at its first idle turn
kind: change
priority: P1
deps: []
created: '2026-11-01T01:40:26Z'
---
SubagentStop fires whenever a subagent's turn ends without a tool call (waiting on a background build or Monitor, or before the [handback-send-enforce] nudge); hook.end_run marks the run ended then and ignores every later stop (if r.get('ended'): return). The agent is then resumed (by the background-task notification or the enforce nudge) and keeps working, so the record holds a mid-work last line and the wrong usage/record, and the pass treats the change as having no live run and lists a second one beside it.
Evidence:
- server-world-entities-2: ended 00:29:22Z with last 'I'll wait for the build notification.'; its transcript continues to 00:32:39Z (build notification 00:31:24, track.sh up/down, hd handover 488270104 at 00:32:30, SubagentHandback 00:32:35). Meanwhile server-world-entities-3 was listed 00:32:11Z and started 00:32:44Z on the same change.
- quest-cooksassistant-2: ended 01:36:46Z with last 'The monitor is armed; I'll continue when the fix lands.'; at 01:36:46 the enforce nudge resumed it, it wrote handoff.md, TaskStop'ed its monitor and handed back 'run quest-cooksassistant-2: handoff' at 01:37:13Z, after the record was closed.
- Same mid-work last lines on harness-server-build-musicrepository-1 ('Waiting for the build to finish.', -2 listed 3s later), harness-no-powershell-1, server-friends-chat-clan-channels-4, harness-client-measure-repo-root-1; ~40 more ended runs carry a last line that is not the 'run <name>: ...' hand-back.
The run should end on its hand-back (SubagentHandback delivered) or on the last SubagentStop: a later stop of the same agent refreshes ended/usage/last/record, and a run whose agent is resumed is alive for the pass. One test per requirement touched.
