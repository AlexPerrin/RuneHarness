---
slug: harness-orchestrator-drives
track: harness
title: The orchestrator drives the loop; main is only the chat interface
kind: change
priority: P0
deps: []
created: '2026-11-01T03:28:56Z'
---
The user's word: the orchestrator was meant to do what main does now, splitting agent orchestration and monitoring from the chat interface. Today main (the head, skill head) runs hd, spawns and stops every run, commits definitions, ends stale runs by hand, sets aside duplicate listings and relays hand-backs; the orchestrator is a one-shot monitor. Target: one long-lived orchestrator owns the loop: it arms the wake watch, runs hd, spawns and stops runs, commits definitions, handles hand-backs and files harness changes. Main only relays the user's messages (answers, approvals, instructions) to it and shows it cards and questions. Constraint to design around: in Claude Code a subagent cannot spawn subagents, so the orchestrator must be its own top-level session with the Agent tool (for example a local session main messages with SendMessage, or a headless claude process). Approvals stay the user's word recorded by main (hd approve and hd close stay main-only). Rewrite PROBLEM, PRD and ARCHITECTURE for the split, the head skill to relay-only, and orchestrator.md to the driver role. This is a major revision: the cutover to it needs the user's yes. One test per requirement touched.
