---
slug: harness-dep-reopen-ends-run
track: harness
title: A started run goes on after its dependency reopens
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T07:51:16Z'
---
Monitor sweep 56 P3-a: server-clan-guest-4 (dev) kept running after its change went to 'waiting on server-clan-channels' at 07:44:14Z, when that dependency reopened for the user's split, holding 6 desktops and server-/http-server-clan-guest; only the idle hook (hook.py:613, 07:49:25Z) told it to go down. The dependency wait step (hd.py:1472-1477) carries no stop, and hd.py:818-819 ends only an unstarted listing, so a started run whose dependency reopens works on against a moving base. Acceptance: when a started run's change waits on a dependency that reopened (not a mere re-gate of an unchanged dep), the run ends at its next step with a hand-off; a re-gating dependency still leaves it running.
