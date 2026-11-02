---
slug: harness-no-join-into-depended
track: harness
title: A change that others wait on takes no joined filing until it ships
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T21:31:23Z'
---
Sweep 87 P2-a: harness-filestore-track-1 filed its flaky-test limit as harness-attempts-test-mtime-flake (state/events.jsonl:11549, 21:22:37), filestore became its dependent (11550); 3 minutes later the orchestrator's sweep-86 filing (deps_held rewrite) was routed by mechanism loop into that same change (11560), so filestore (handed over cb682c3 21:26:09) waits on a one-test flake fix shipping with a rewrite it never needed. merge_limit (hd.py:3627-3640) joins any filing to the open change of its mechanism without checking for dependents (limit-of / deps). P4-a, same root: harness-attempts-test-mtime-flake (loop) and harness-tree-transitive-central-2 (tree) now both edit deps_held (hd.py:1622-1644) in parallel worktrees: the mechanism is the filer's label, not ownership of the code. A change with waiting dependents takes no join (the filing opens its own change or waits behind it). Evidence: evidence/monitor/sweep-87.md
