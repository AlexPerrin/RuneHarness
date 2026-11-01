---
slug: harness-ci-boot-port-in-use
track: harness
title: The fork CI's server boot never fails on a port already in use
kind: change
priority: P1
deps: []
created: '2026-11-01T14:07:56Z'
---
Hand-back of server-token-auth-8 (2026-11-01): CI run 41312919759 on gate commit d343bb871 failed the server boot with java.net.BindException: Address already in use (rsprot's bind); gate commit 19c186c08, same tree, passed in run 41310486719. A gate verdict that flips on the same tree is not an observed fact about the code. Suspected (not checked): game port 43594 is inside the runner's ephemeral port range. Acceptance: the CI boot step binds a port no other process on the runner can hold (e.g. a free port chosen at boot, or the ephemeral range moved off it); the cause is confirmed from the runner; a test or CI check covers it.
