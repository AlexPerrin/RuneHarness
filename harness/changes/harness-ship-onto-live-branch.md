---
slug: harness-ship-onto-live-branch
track: harness
title: 'A harness change cannot ship: its base is main while the live checkout is
  v8'
kind: change
priority: P0
deps: []
created: '2026-10-31T23:57:41Z'
---
Ship of harness-build-volume-perms and harness-file-maintainer-findings: 'fatal: Not possible to fast-forward, aborting.' (state/<slug>/ship.log). The harness track's base is the repo's default branch, main, which is v7 (it holds an extra docs/V8-BRIEF.md commit); the live checkout ~/osrs-harness is on v8, and v8 also moves with the head's own commits (hd new definitions) while a change gates. T is built on main and cannot fast-forward v8. Earlier ships (harness-client-track-root, harness-parallel-spawn-binding) died twice on 'refused: has uncommitted edits' and are not retried. Fix: the harness base is the live checkout's branch; ship lands T on it when the live branch has not moved past the gated base, else the change re-gates on the new base; the definitions the pass or hd new writes do not block ship. After landing, re-ship the stuck changes. One test per requirement touched. Land this change by hand (fast-forward v8 after the suite is green), since ship itself is what it fixes.
