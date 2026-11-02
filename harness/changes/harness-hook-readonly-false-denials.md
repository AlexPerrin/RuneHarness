---
slug: harness-hook-readonly-false-denials
track: harness
title: The hook lets read-only gh api -X GET with -f and hd.py --help through
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T14:55:36Z'
---
Sweep 57 P4-c: a reader's 'gh api -X GET search/code -f q=...' was denied as 'reader writes' (08:08:19Z): the -f alternative in WRITES (hook.py:~488) matches despite -X GET, while the denial text says gh api GET is allowed. A qa's 'python3 hd.py --help' was denied as 'hd pass in a subagent' (14:50:23Z): the regex at hook.py:365 counts it as a pass, but main() (hd.py:3335) only prints usage. Evidence: evidence/monitor/sweep-57.md
