---
slug: harness-planner-listing-follows-trigger
track: harness
title: an unspawned planner run goes once its triggers are carried, like any change's
  unspawned run
kind: change
priority: P1
mechanism: goals
deps: []
created: '2026-11-02T18:03:48Z'
---
planner-32 was listed at 16:09:13Z (events.jsonl:10359) on 'live: ship ended 3 times without a result since 2026-11-02T16:04:13Z (state/live/ship.log)'. 27 s later the orchestrator filed harness-live-http-mount (16:09:40Z, events.jsonl:10360), whose body names state/live/ship.log, so plan() no longer wants a planner on it. The listed run stayed and was spawned at 18:01:03Z (events.jsonl:10487) with nothing to file. Root cause against PRD (a run exists for a due step; the planner acts on a new fact): the pass ends or relists an unspawned run once its step is no longer due (the per-change loop in the pass, 'no longer due' / 'relisted', hd.py ~2596-2611), but the planner is a pseudo-change built in plan() (hd.py ~2288) outside that loop, so its listed run is never reconciled. Fix at the root: the planner's unspawned run follows the same rule as any change's: plan() (or the loop it shares) relists it on the current input when why is non-empty and different, and ends it 'no longer due' when why is empty; no planner-specific rule beside the shared one. Acceptance (a test in plan's R class): a planner run listed on an alert whose subject an open change's body then names ends unspawned on the next pass; one listed on two triggers of which one is carried is relisted on the other.
