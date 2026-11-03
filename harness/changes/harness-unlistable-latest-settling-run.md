---
slug: harness-unlistable-latest-settling-run
track: harness
title: the no-loop predicate reads the latest run and only a settling record
kind: change
priority: P0
deps: []
created: '2026-11-01T18:50:11Z'
---
unlistable() (hd.py ~line 999) stalls two changes for good, alerting "handed back its record, yet its step is still due on the same input: no run is listed":
1. Order: ctx.runs come from sorted(glob("*.json")) (line 360), filename order, so same[-1] is quest-restlessghost-9 although quest-restlessghost-10 is later ("-10" < "-9"; likewise "-100" < "-11"). state/runs/quest-restlessghost-9.json: qa, input ["f04f822fb765138806c148a5dc5e9dca9b0448d9", "61fc60ddee24", []], record True, handoff_told 167206 (a context-limit hand-off). state/runs/quest-restlessghost-10.json: qa, same input, record False, reason "console died". The latest run on the input had no record, so one retry is due, not a stall.
2. Deferring records settle nothing: a hand-off record (qa-9 above; handoff.md is unlinked at the next handover, so the exemption at line 1004 lapses) and a dep record. client-down-stops-mobile-login-1: input ["", "e130103fe1ca", 0], record = filed dep harness-down-stops-mobile-login (event "dep" 2026-11-01T04:13:36Z, then "waiting on harness-down-stops-mobile-login"); the dep went done at 04:17:04Z and the step is "dev run due" on the same input since 04:17:08Z, never listed again.
Fix: pick the latest run by its listed time, and count as settling only a record that answers the step (handover, verdict, contract, ask, filed change) on that input; a hand-off or a dep the run filed (now done) leaves the step listable. Proof: tests for both shapes; then hd lists a qa run for quest-restlessghost and a dev run for client-down-stops-mobile-login (each when its tier hold allows), and both alerts clear.
