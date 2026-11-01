---
slug: harness-runs-never-idle
track: harness
title: Runs never end a turn while their own work is still running
kind: change
priority: P1
deps: []
created: '2026-11-01T03:14:34Z'
---
The user counted 7 paused agents (2026-11-01). Devs and qa start builds, ups and device runs in the background, then end their turn 'waiting on background work'. They sit paused for up to 1.5 h (cannon-review-354-7 since 02:09Z). They can't be told apart from a stuck run, and they hold their slot. In .claude/agents/dev.md and qa.md: run your own builds, ups and device steps in the foreground, or block on them with a single until-loop on an observable fact (a file, a log line, a port). Never end a turn while your own process is running. A step that cannot finish (a hang, a refused login) is an error to hand off, not a reason to idle. The head also stops each agent as soon as its hand-back arrives. One test per requirement touched, if a hook can check it, for example SubagentStop refusing a stop while the run's own background processes are alive.
