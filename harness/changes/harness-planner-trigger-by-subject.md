---
slug: harness-planner-trigger-by-subject
track: harness
title: 'a planner trigger is the subject an alert names, not its text: a reworded
  or recounted alert of a filed fault lists no planner'
kind: change
priority: P1
mechanism: goals
deps: []
created: '2026-11-02T02:42:29Z'
---
planner-21 (State: 'server-cache-clientscript-name-hash: ship died twice without a result (state/server-cache-clientscript-name-hash/ship.log)') filed its fix into harness-carry-gh-pr-edit-classic-projects (open, mechanism carry; its body names that log and 'ship died twice without a result'). fc7e88b reworded start()'s alert (hd.py:1198) to 'ended 3 times without a result'; planner-23 was listed at 02:38:30Z on 'server-cache-clientscript-name-hash: ship ended 3 times without a result (state/server-cache-clientscript-name-hash/ship.log)' with nothing to file: the fix is that open carry change (in dev, tools conflict in tools/gate/gate.sh). Root cause against PRD (the planner acts on a new fact; one fact, one change): plan() (hd.py:2003) leaves a trigger out only when its exact text is in an open change's body or in a recorded planner run's input, so a count or wording change of the same fault is a new trigger. This replaces plan()'s rule 'it lists the planner again only when it changes (... an alert with a new count)': an alert's identity is its subject (the process log it names, state/<slug>/<name>.log; a gate failure's change and T); it is carried while an open change's body names that subject, and handled once a planner run handed back on that subject since start() last reset that process's count (new args, key, result or script). Acceptance (a test in plan's R class): a recounted or reworded alert of a subject an open change's body names, or a planner handed back on since the last reset, lists no planner; the same process failing again after its count reset lists it.
