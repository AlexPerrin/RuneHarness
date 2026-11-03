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

Also (filed): A harness dev runs the whole harness suite before hand-over
Sweep 59 P3-a: harness-orchestrator-self-restart (bdf4925, ran R2/R5/R6 only) failed R7's view-section test and harness-ci-restart-same-head (fd2a438, ran R4 only) failed R5's GitHub-writes allowlist test; the batch gate needed 6 cycles (~12 min, 15:00-15:12Z) to ship 3 of 5 (state/ship-harness/tests.txt, events.jsonl 9883-9892). The whole suite runs in ~51 s (246 tests), so on the harness track targeted tests cost more than they save. Evidence: evidence/monitor/sweep-59.md

Also (filed): A hand-over that names its own limits in prose is not accepted as Limits: none
Sweep 59 P3-b: harness-orchestrator-self-restart-1 (14:57:13Z) and harness-dep-reopen-ends-run-2 (15:10:37Z) handed over 'Limits: none' while their hand-back and notes listed unchecked risks of their own change; the orchestrator joined them back (6f1fbf7, 92ac57c), costing a full extra dev and gate round each. dev.md:23-27 forbids it but nothing enforces it; the run should fix its own limits before handing over. Evidence: evidence/monitor/sweep-59.md
