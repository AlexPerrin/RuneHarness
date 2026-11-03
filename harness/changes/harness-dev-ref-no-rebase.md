---
slug: harness-dev-ref-no-rebase
track: harness
title: Dev refs get rebased after they are pushed
kind: change
priority: P1
deps: []
created: '2026-11-01T00:17:46Z'
---
While v8 moves, harness devs rebase their dev ref onto it. When that ref is already on origin, the rebased commit needs a force push. harness-file-maintainer-findings-2 and harness-dupe-tests-row-scope-2 were denied it. harness-definitions-no-regate-1 force-pushed its own dev ref (harness/harness-definitions-no-regate), against the rules. Pick one rule and state it in .claude/agents/dev.md and tools/track.md: either harness dev refs stay local, since hd reads the local ref, or a dev merges v8 into its ref instead of rebasing. One test per requirement touched.
