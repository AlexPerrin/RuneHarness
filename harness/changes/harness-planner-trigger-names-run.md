---
slug: harness-planner-trigger-names-run
track: harness
title: 'a planner trigger''s subject is the change or run an alert names: an alert
  of a run an open change already names lists no planner'
kind: change
priority: P1
mechanism: goals
deps: []
created: '2026-11-02T05:28:36Z'
---
planner-28 was listed at 05:26:50Z on 'server-clan-channels: qa run server-clan-channels-4 handed back its record, yet its step is still due on the same input: no run is listed' and the same line for server-clan-guest-2. planner-27 (listed 05:21:26Z on the server-examine-multi-transform-2 line of the same fault) had already filed it into harness-taskstop-ends-scoped-bash, whose body names server-clan-guest-2 and server-clan-channels-4 and whose dev run harness-taskstop-ends-scoped-bash-1 is live; the clan alerts appeared at 05:22:37Z, after planner-27 was listed, so a second planner run had nothing to file. Root cause against PRD (the planner acts on a new fact; one fact, one change): trigger() (hd.py ~2114) reduces only a process-log alert to its subject; any other alert is its whole text, so it is carried only when an open change's body quotes that exact line. Fix in trigger(): an alert's subject is what it names, a process log (state/<slug>/<name>.log), else the run it names (<change>-<n>), else its change and T for a gate failure; carried while an open change's body names that subject, handled once a planner run handed back on it. This replaces the exact-text fallback of trigger(). Acceptance (a test in plan's R class): an unlistable-step alert whose run an open change's body names lists no planner; the same alert for a run no open change names lists one.
