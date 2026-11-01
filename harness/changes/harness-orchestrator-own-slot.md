---
slug: harness-orchestrator-own-slot
track: harness
title: The orchestrator run is listed even when every agent slot is taken
kind: change
priority: P1
deps: []
created: '2026-11-01T01:01:56Z'
---
Fact that repeats: three times main spawned an orchestrator by hand, outside the pass, because the agent cap left no slot, so the run had no record, brief, usage or hand-back check. Evidence (state/events.jsonl):
- line 257 {"action": "stop-unmatched", "agent": "aeb9c3a81a271fdb2", "role": "orchestrator", "ts": "2026-11-01T00:04:40Z"}; its prompt: "The pass did not list you because all agent slots are in use, so this prompt is your brief."
- line 390 {"action": "stop-unmatched", "agent": "a873d219fbed9edf7", "role": "orchestrator", "ts": "2026-11-01T00:13:05Z"}; prompt: "All agent slots are in use, so this prompt is your brief."
- line 978 {"action": "stop-unmatched", "agent": "a50246d7eeebfd2b3", "role": "orchestrator", "ts": "2026-11-01T00:58:25Z"}; prompt: "All agent slots may be in use, so this prompt is your brief."; it stopped unfinished (meta has no finished), last text "Writing the inventory and filing the changes."
(transcripts: ~/.claude/projects/-home-alex-osrs-harness/39cfb040-0727-4395-9cdf-aab5eab82896/subagents/agent-<id>.jsonl)
Cause: hd.py dispatch() returns when runs alive >= cfg.agents (hd.py:714), and orchestrate() goes through dispatch, so the run that files the remedies for the blocked work waits behind that work; hook.py end_run() then logs the hand-made agent as stop-unmatched.
Fix with one mechanism: the orchestrator run is outside the agent count (it is at most one alive, it writes no product code and holds no device), so orchestrate() lists it whenever its facts call for it; and a planning request from the user reaches it as a goal or alert on that same path, so main never spawns an orchestrator without a brief. One test per requirement touched (R2/R6 dispatch).
