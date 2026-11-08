---
slug: h-judge-needs-deploy
track: harness
priority: P2
---
# a criterion judged only after deploy (acc-11, mobile sign-in through Central) can never be judged: deploy follows PASS and qa may not touch a mobile on a fork up



## alert 59 fault 209 (×1, first 2026-11-08T01:20:28+00:00)
central-game-session acc-11 (G11, the official Android app signs in through Central) can be judged only once the change is deployed to staging/live, but deploy follows a PASS verdict and qa may not touch a mobile on a fork up (tracks/fork/track.md Never): the criterion can never pass before the verdict that gates its deploy. It needs a post-deploy check (or a fork up with a mobile) instead of a pre-verdict judged row.
