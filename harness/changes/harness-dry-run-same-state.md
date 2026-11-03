---
slug: harness-dry-run-same-state
track: harness
title: check-dry-run compares both passes over one state snapshot
kind: change
priority: P1
deps: []
created: '2026-11-01T18:13:04Z'
---
The dry-run gate failed twice on a harness-made row while nothing in the candidate touched an upstream step:

    18:08:34Z harness-handoff-replacement-spawns: FAIL: dry-run ... plans a public act main does not: change: cannon-review-354 [server P2]: shipping upstream
    18:10:46Z harness-handoff-replacement-spawns: FAIL: dry-run ... (same line)

cannon-review-354 got its approval at 18:08:23Z and its ship (hd-public upstream) started and died twice in that window (state/cannon-review-354/proc-ship.json attempts 2). Rerun afterwards, both `hd.py tick --dry-run` (live) and the build copy's (b7bf2e99e onto fda21dd3e) print the same `shipping upstream` line: the divergence was the state moving between the two sequential dry-runs in tools/track.sh check_dry_run, not the candidate's code. Acceptance: both dry-runs read the same state (e.g. one copy of state/ taken once and passed as HD_ROOT to both), so a public act starting or ending mid-gate cannot fail a candidate; the R test covers: state changing between the two reads does not fail the check, and a candidate whose code plans an extra act still fails it.

Orchestrator note: harness-handoff-replacement-spawns 8d5423a already changes check_dry_run to take main's plan before and after the candidate and fail only on an act neither plans; this change is done when that ships and the R-test for it exists.
