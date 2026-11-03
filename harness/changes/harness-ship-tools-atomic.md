---
slug: harness-ship-tools-atomic
track: harness
title: Ship ignores a failed tools-branch fast-forward and moves the live branch anyway
kind: change
priority: P0
deps: []
created: '2026-11-01T00:27:48Z'
---
tools/track.sh ship() loops over TOOLS and runs `git -C $wt merge -q --ff-only $sha && echo ...` with no exit on failure, then fast-forwards and pushes v8. When a tools branch moved after the gate, ship partly lands. Only the live-branch check (merge-base --is-ancestor HEAD $tc) re-gates; the tools branches get no such check.
Evidence: harness-jav-config-local-only, handover.json tools {client 90ad1f9a0, fork 5b2fddddc}, T 4405f50. state/harness-jav-config-local-only/ship.log, twice: "client/harness-v8 at 90ad1f9a0" / "fatal: Not possible to fast-forward, aborting." / "v8 at 4405f50". Fork local/harness is at a001a05ea (harness-server-measure-goal-dir shipped there in between), so 5b2fddddc diverges from it. Result: v8 and client/harness-v8 hold the change and local/harness does not. The ship died twice (alert) and the pass is now re-building and re-gating T f22952027.
Fix: before moving anything, check that every tools branch and the live branch are ancestors of their carried heads. If any is not, re-gate (the same exit as the live-branch case, which then sends the dev to merge the moved tools branch). Any ff failure exits non-zero before v8 moves. One test per requirement touched (R8).
