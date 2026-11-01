---
slug: harness-dev-delegates-reads
track: harness
mechanism: roles
title: Dev and QA runs delegate read-heavy work to a read-only reader role; nested
  agents are part of their parent run
kind: change
priority: P1
deps: []
created: '2026-11-01T21:57:49Z'
---
The user's word (2026-11-01): "dev agent shoukd be able to spawn its own subtasks for token efficiency, eg the server dev will use a read only agent to parse the psprox dumps." dev.md and qa.md already say 'Read-heavy lookups (recordings, cache dumps, decompiled code, CI logs) go to a read-only subagent that returns the conclusion', but: runs often do the reading themselves (e.g. goblin-367-rsprox-dump-2 transcribed and read the whole recording itself; several runs hit the context limit mid-read); there is no read-only role, so a nested agent gets every tool; and a nested agent's hand-back reached the orchestrator (the 'Find e2e flake output' agent spawned by harness-e2e-test-flaky-1 reported to the orchestrator after its parent was stopped). Acceptance: (1) a 'reader' agent type in .claude/agents/ with read-only tools (Read, Grep/Glob, read-only Bash such as track.sh recordings/transcribe output reads, gh api GET, the osrs-mcp wiki/cache tools), no Edit/Write/Agent, returning a conclusion under a stated size; (2) dev.md and qa.md name it with the concrete cases: RSProx transcripts and recordings, cache/gameval dumps, decompiled code, CI and server logs, wiki transcripts; the run keeps only the conclusion; (3) hook.py treats an agent spawned by a run as part of that run (not a run: no binding, no refusal, no listing), and its SubagentStop goes to its parent, never to the orchestrator; when the parent run ends, its nested agents are stopped; (4) a test covers a nested reader under a dev run: not bound as a run, not refused, stopped with its parent.
