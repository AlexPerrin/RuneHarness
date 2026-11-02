---
slug: harness-dep-on-fork-merge
track: harness
title: a change waiting on another upstream change waits on its fork merge, not its
  upstream merge
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T02:22:52Z'
---
The user (2026-11-01, ET): " server-token-auth waits on central-token-login-op's upstream merge.": we have fork we can test a merge with. We will bundle the upstream auth contribution in the future. Continue to dev work past what is in the contrinution queue. 1. Lift the hold. server-token-auth showed 'waiting on central-token-login-op's upstream merge' while central-token-login-op was held for upstream; dev work stalled behind the contribution queue. A dependency is met once the dep's head is in the fork's integration tree (its gate passed and it is merged and tested there); the upstream merge gates only that change's own upstream card. Upstream contributions that belong together (auth: server-token-auth, central-token-login-op) are bundled into one card later, by the user's word; dev work keeps going past the contribution queue.
