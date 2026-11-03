---
slug: harness-contract-proof-no-dependent
track: harness
title: A contract row never requires proof from a change that depends on it
kind: change
priority: P1
deps: []
created: '2026-11-01T04:27:39Z'
---
central-token-login-op's contract (rows c2-checks, c3-session) required in-game proof through server-token-auth's build; server-token-auth depends on central-token-login-op, so the QA run central-token-login-op-3 had to FAIL rows whose code it proved correct at the world link, sending the change back to a dev with nothing to fix. Expected: a contract (seed rows and the QA contract brief) proves a change only through its own build and its dependencies; proof that needs a dependent change is that change's row. The central track also has no up/down verbs (track.sh down exited 2), so a central change's run cannot be judged live through the track. One test per requirement touched.
