---
slug: harness-docs-tree-conflicts
track: harness
title: Harness changes stop colliding on the shared docs; a sibling's ship costs no
  dev run
kind: change
priority: P1
mechanism: integration-conflict
deps: []
created: '2026-11-01T22:50:06Z'
---
Planner-16 monitor: state/events.jsonl holds 23 'tree conflict: dev' steps since v8 started, over 19 harness changes (harness-spawn-for-ended-run-refused 3 times today: 21:59:38Z docs/ARCHITECTURE.md+tests/test_hd.py, 22:08:25Z docs/ARCHITECTURE.md+hook.py, 22:40:27Z docs/ARCHITECTURE.md). By file: docs/ARCHITECTURE.md 13, docs/PRD.md 6, hd.py 5, tests/test_hd.py 4, hook.py 2. Each conflict sends the change back to a dev run (hd.py step 'tree conflict: dev') with nothing wrong in its own work. Root cause to find against the workflow (a change's T is its dev ref merged onto the live branch): the conflicts are concentrated in the two docs every change must update, so the cause is likely in how the docs take a change's fact (shared paragraphs rewritten per change rather than one fact in its own lines) or in dev refs handed over against an old base; fix it at that cause, no merge-strategy special case for docs. Acceptance: the cause is named with the events above; two sibling harness changes that each add a requirement's fact to PRD.md and ARCHITECTURE.md merge onto the live branch in either order without a conflict (a test); a real conflict (same fact changed two ways) still goes to dev.
