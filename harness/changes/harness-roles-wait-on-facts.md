---
slug: harness-roles-wait-on-facts
track: harness
title: runs wait on time bounds and poll task-output files
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T06:10:20Z'
---
sweep-45 P2-c: cannon-8 repeated 'timeout 175 ... until grep -q broken <task output>' from 05:57Z to 06:09Z; clan-guest-3 looped 'seq 1 100 x sleep 5' over a tail that prints only at the end. The hook denies only 'sleep N; until'. The role files: wait on the fact itself (a foreground track.sh, a devtools wait_for on the game event), never a time-bounded poll of a task's output file. evidence/monitor/sweep-45.md
