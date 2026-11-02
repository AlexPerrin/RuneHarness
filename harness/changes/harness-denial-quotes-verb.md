---
slug: harness-denial-quotes-verb
track: harness
title: A hook denial's event names the verb it denied
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T19:17:10Z'
---
Sweep 71 P5-a: events.jsonl:10906 (19:12:14Z) records 'reader writes: ; D=/tmp/claude-1000/...' for 'D=<scratchpad>/rsprot; mkdir -p $D && cd $D && unzip ...' (a correct denial). WRITES' AT prefix (hook.py:515) matches env assignments with \w+=\S*\s+, and \S* runs across ';', so m[0] starts with the assignment and the [:60] cut (hook.py:543) drops mkdir. Cosmetic: the reader's reason quotes the whole match. Evidence: evidence/monitor/sweep-71.md
