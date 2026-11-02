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
