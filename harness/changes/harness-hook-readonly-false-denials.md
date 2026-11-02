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

Also (filed): dev.md names track.sh test and hd tick --dry-run among steps never wrapped in timeout
Sweep 58 P4-b: the hook denied 'timeout 600 tools/track.sh test' 13 times today (e.g. 14:51:36Z, 14:54:24Z, 14:55:03Z, 14:55:35Z across four harness dev transcripts), all valid, each a lost turn; dev.md:29-32 states the no-timeout rule only for builds, ups and mobile or desktop steps. Evidence: evidence/monitor/sweep-58.md
