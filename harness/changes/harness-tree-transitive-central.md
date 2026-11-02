---
slug: harness-tree-transitive-central
track: harness
title: A server change on another change's head builds with that change's Central
  dependencies
kind: change
priority: P1
mechanism: tree
limit-of:
- server-token-refusal-logged
deps: []
created: '2026-11-02T21:09:53Z'
---
Found by server-token-refusal-logged-2. server-token-refusal-logged (deps: []) is, per its contract c6 and R8, a head on top of dev/server-token-auth (whose deps hold central-token-login-op). Its build T (hd tree: base + head, Central part '') holds server-token-auth's code, which needs dev.or2:openrune-central/central-common/central-worldlink 2.0.3 from Central's tree, but Ctx.central(ch) reads only the change's own direct deps of track central, so the build fails at dependency resolution (state/server-token-refusal-logged/build-c19af88a44f900611e76a2df9f5613b0a1150c3e-9bb2bb0525dc-1.log: Could not find dev.or2:openrune-central:2.0.3), and a test, up or gate of the change can never run. Root cause: the dependencies T, central() and the order use are the definition's direct deps only; a change whose head holds another open change's head (R8: a same-track dependent joining that change's PR), or whose dep has its own deps, loses them. Fix at R8: the dependency set hd uses for a change is the closure of its deps, with each open same-track change whose head the change's head holds counted as a dep, so T merges and central() includes every Central head the code needs. Acceptance: hd tree server-token-refusal-logged <its head> prints a Central part equal to server-token-auth's, and tools/track.sh build server-token-refusal-logged succeeds; a test in tests/test_hd covers a dependent on a dependent with a central dep and a head built on an open change's head.
