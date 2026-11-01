---
slug: harness-orchestrator-reloads-own-definition
track: harness
title: When the orchestrator's own definition ships, the running orchestrator hands
  off to a fresh session on it
kind: change
priority: P1
mechanism: orchestrator
deps: []
created: '2026-11-01T23:07:29Z'
---
Monitor sweep 8 (2026-11-01 23:06Z): harness-orchestrator-never-blocks shipped at 23:01:09Z (disallowedTools: AskUserQuestion in .claude/agents/orchestrator.md), but the live orchestrator (pid 2280990, up 40,966 s since ~11:38Z) loads its frontmatter and prompt only at start, so it runs the old definition; harness-orchestrator-runs-monitor likely the same. Root cause against R1: for the orchestrator's definition the live target is the running session, and no ship reaches it. Acceptance: a pass that sees the shipped orchestrator.md blob differ from the one the running orchestrator started on raises one step for it: write its hand-off (open questions, running agents, the monitor sweep in progress) to state/orchestrator-handoff.md, then the session is replaced by a fresh 'claude --agent orchestrator' that reads the hand-off at step 1; runs keep running across the swap; a test covers the blob change raising the step.
