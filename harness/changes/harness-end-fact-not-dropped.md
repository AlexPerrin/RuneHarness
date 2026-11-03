---
slug: harness-end-fact-not-dropped
track: harness
title: A run that handed back keeps its end fact when the pass also ends it
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T21:00:58Z'
---
Sweep 84 P4-a: the hook writes the ended event at once (hook.py:370) but its end fact folds a pass later; a pass that sees the handover first moves the step to a wait and settle (hd.py:2310-2325) ends the run with a pass reason and a second ended event, then apply_fact drops the end fact because reason is set (hd.py:886-889): usage and last are never recorded, and unlistable() (hd.py:2253-2254) never counts the run as a try. harness-ask-settle-baseline-1 events.jsonl:11366-11367 (state/runs/harness-ask-settle-baseline-1.json reason 'waiting for the batch ahead', last None); also levelup-2 (10813/10821), denial-quotes-verb-1 (10964/10967), reader-git-readonly-1 (10695/10708), carry-gh-pr-edit-classic-projects-4 (7961/8037). Evidence: evidence/monitor/sweep-84.md
