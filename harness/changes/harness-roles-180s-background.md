---
slug: harness-roles-180s-background
track: harness
title: The roles describe the 180 s backgrounding, not a 600 s limit
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T20:45:25Z'
---
Sweep 83 P4: .claude/agents/dev.md:30, qa.md:13 and hook.py:510's timeout denial say Bash timeout 600000 is the call's limit, but Claude Code moves a subagent's foreground command to the background after 180 s whatever timeout it asks. This session's subagent transcripts hold 92 'moved to the background ... after running for 180s' results (40 until waits, 29 track.sh, 17 other); 14 times the agent TaskStopped the backgrounded wait and reissued it (server-clan-guest-6, agent-a40d2a8d91d5e6df3.jsonl, 20:33:03-20:40:11); agents learned to pass 170000. State that a command still running at 180 s keeps running in the background and the agent waits on its task notification. Evidence: evidence/monitor/sweep-83.md
