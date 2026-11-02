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
- server-token-auth
deps: []
created: '2026-11-02T21:09:53Z'
---
Found by server-token-refusal-logged-2. server-token-refusal-logged (deps: []) is, per its contract c6 and R8, a head on top of dev/server-token-auth (whose deps hold central-token-login-op). Its build T (hd tree: base + head, Central part '') holds server-token-auth's code, which needs dev.or2:openrune-central/central-common/central-worldlink 2.0.3 from Central's tree, but Ctx.central(ch) reads only the change's own direct deps of track central, so the build fails at dependency resolution (state/server-token-refusal-logged/build-c19af88a44f900611e76a2df9f5613b0a1150c3e-9bb2bb0525dc-1.log: Could not find dev.or2:openrune-central:2.0.3), and a test, up or gate of the change can never run. Root cause: the dependencies T, central() and the order use are the definition's direct deps only; a change whose head holds another open change's head (R8: a same-track dependent joining that change's PR), or whose dep has its own deps, loses them. Fix at R8: the dependency set hd uses for a change is the closure of its deps, with each open same-track change whose head the change's head holds counted as a dep, so T merges and central() includes every Central head the code needs. Acceptance: hd tree server-token-refusal-logged <its head> prints a Central part equal to server-token-auth's, and tools/track.sh build server-token-refusal-logged succeeds; a test in tests/test_hd covers a dependent on a dependent with a central dep and a head built on an open change's head.

Also (server-token-auth): The stacked check blames the change another head is built on
server-token-auth's head e40d5e9dd holds only its own five commits on upstream main 049a26312, yet hd puts it in 'stacked on server-token-refusal-logged: dev'. server-token-refusal-logged's head 139f119d6 is e40d5e9dd plus one commit (it edits TokenLoginVerifier, which server-token-auth adds) and its definition lacks server-token-auth in deps. stacked() (R8) flags any open same-track change whose unmerged commits intersect the head's, in both directions, so the base is told to rebase or add its dependent to deps: neither is possible (its head has nothing else to drop; the dep would be a cycle). Root cause: the check has no direction. A head is stacked on o only when it reaches commits of o beyond its own: when o's unmerged set strictly contains the head's (o descends from the head), o is stacked on it, and o's own step (add the base to deps, then join its PR) is the remedy. Fix in stacked(): skip o when mine < theirs; a partial overlap or equal sets still flag both. Acceptance: a test in the R8 class where B's head descends from A's head with no dep: A is not stacked, B is stacked on A.
