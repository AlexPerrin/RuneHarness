---
slug: harness-docs-line-merge
track: harness
title: Changes editing different facts of the source docs merge without conflict
kind: change
priority: P1
mechanism: tree
deps: []
created: '2026-11-01T23:50:54Z'
---
Found by monitor sweep 13 (evidence/monitor/sweep-13.md, B1). docfmt gives one fact per line, but git still conflicts on neighbouring hunks: at 23:40:02 three harness changes went to tree conflict in PRD.md/ARCHITECTURE.md; at 23:47:13 tools-pinned-per-process conflicted again on PRD.md:164 (run-stop edited the 'hd stop' line; tools-pinned inserted a line before it) - its 5th dev run. harness-docs-tree-conflicts' acceptance (only the same fact changed two ways conflicts) does not hold. Acceptance: a merge of two changes that touch different fact lines of docs/*.md succeeds without a dev run (a line-level merge driver checked by docfmt, or the loop resolving docs-only conflicts itself); only the same fact line changed two ways is a tree conflict; a test replays the PRD.md:164 case.
