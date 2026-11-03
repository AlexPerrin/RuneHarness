---
slug: harness-hook-denies-self-pgrep
track: harness
title: a run's self-matching pgrep wait is only role text; the hook does not deny
  it
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T05:43:52Z'
---
sweep-43 P2-a: the rule shipped at 05:25:53Z is in the role files only; runs started before it keep spinning (cannon-8 pgrep -f 'track.sh restart cannon-354' 05:28:59Z; hunter-18 until ! pgrep -f 'track.sh up hunter-feat-pr' 05:32:21Z, backgrounded, pid 2157757, 11 min with no up behind it). hook.py runs from disk, so a PreToolUse deny of a run's Bash whose pgrep -f pattern is a substring of the command itself reaches live runs too. evidence/monitor/sweep-43.md
