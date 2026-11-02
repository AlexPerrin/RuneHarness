---
slug: harness-taskstop-ends-scoped-bash
track: harness
title: TaskStop of a Bash that hd scope moved into a run scope leaves the shell running
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T05:18:04Z'
---
sweep-41 P1-a': server-clan-channels-4 TaskStopped 7 background tasks (beqso35os ... bmx3hezeb); Claude Code marked them killed, but the shells, moved by 'hd scope' into hd-server_clan_channels_4-<pid>.scope, kept running until the run pkill'd them at 05:15:08Z. A TaskStop of a scoped Bash stops its scope. evidence/monitor/sweep-41.md

Also (filed): a run ended for a wait loses its hand-off, and a met dependency re-gating ends dev work
server-clan-guest-2 (dev) was ended mid-work when hd marked its change 'waiting on server-clan-channels' (a dependency that had been met and was re-gating); the hook then refused every tool call, so the run could not write evidence/server-clan-guest/handoff.md (the orchestrator wrote evidence/server-clan-guest/handoff-run2.md from its report) and its first build died exit 144. server-clan-channels-4 and server-examine-multi-transform-2 were ended the same way at 05:20:31Z. An ended run may still write its evidence and hand back; and a dependency that was met and only re-gates (tools ship, new head of the dep) does not end a dependent's started run — only a wait that blocks the run's work (an open question, an unmet dependency) does.
