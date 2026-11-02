---
slug: harness-dep-on-fork-merge
track: harness
title: a change waiting on another upstream change waits on its fork merge, not its
  upstream merge
kind: change
priority: P1
mechanism: loop
deps:
- harness-runs-proportionate
created: '2026-11-02T02:22:52Z'
---
The user (2026-11-01, ET): " server-token-auth waits on central-token-login-op's upstream merge.": we have fork we can test a merge with. We will bundle the upstream auth contribution in the future. Continue to dev work past what is in the contrinution queue. 1. Lift the hold. server-token-auth showed 'waiting on central-token-login-op's upstream merge' while central-token-login-op was held for upstream; dev work stalled behind the contribution queue. A dependency is met once the dep's head is in the fork's integration tree (its gate passed and it is merged and tested there); the upstream merge gates only that change's own upstream card. Upstream contributions that belong together (auth: server-token-auth, central-token-login-op) are bundled into one card later, by the user's word; dev work keeps going past the contribution queue.

Also (filed): a wait cycle through a user hold shows as plain 'waiting' and raises no question
sweep-23 P1-a: server-token-auth showed 'waiting on central-token-login-op's upstream merge' (public() hd.py:1573-1579) while central-token-login-op was held by the user until auth lands; the cycle check (hd.py:875, deps_held 1302) sees no hold edge, so nothing asked the user. A hold that closes a wait cycle raises one question naming the cycle. evidence/monitor/sweep-23.md

Also: moved to its own P0 change harness-runs-proportionate (a distinct root cause; joined here by mechanism only).
