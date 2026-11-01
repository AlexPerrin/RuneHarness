---
slug: harness-build-key-and-stale-gates
track: harness
title: A build is keyed only on what it runs; a gate whose key moved is stopped; the
  state names the process actually running
kind: change
priority: P0
mechanism: build-gate
deps: []
created: '2026-11-01T23:32:43Z'
---
Monitor sweep 11 (2026-11-01 23:32Z): the server build key hashes tools/gate/gate.sh, which holds both build code and gate-ci code, so a gate-ci or gradle-volume edit rekeys every build: all 10 server changes went back to 'building' at 23:24:49 (tools 4acc781) and 23:30:57 (66a94c3); state/server-world-entities has 33 build logs for one tree 1fc56bf. ctx.start (hd.py:825) returns as soon as a process with that name is alive, even with other arguments, so a gate whose key moved is never stopped: 10 gate-ci pollers kept the old loop after 23:30:28, the server-world-entities gate from 23:14 (pid 1045784) ran 17+ min while its new build (pid 1219113) waited on flock build.lock. And hd.py:1319 writes 'gate on <new prefix key>' for both batch members while pid 1218823 was gating the older one-member prefix 1d832b0, so a multi-member batch never gates while members keep arriving. Root cause against PRD: keys cover code the build never runs, and an outdated process is not a fact the pass acts on. Acceptance: build and gate code are separate files with separate keys (a gate-ci edit never rekeys a build); a running build/gate/ship whose key is no longer current is stopped (its scope) and the current one started; the state names the key of the process actually holding proc-<role>; a test covers each.

Also (filed): A carried tools head that no longer fast-forwards is rebased by the loop, not by a dev run
The user's word (2026-11-01): fix the churn where harness-tools-pinned-per-process needed four dev runs that only rebased, because the fork's tools branch (local/harness) moved each time a sibling's tools shipped; harness-live-deploy-evidence, harness-github-reads-budget and others did the same (each rebase is a full dev run: brief, worktree, tests, hand-over). Root cause: a change carries its own commit on each tools repo, and the batch only merges harness dev refs; a carried tools head that is no longer a fast-forward of the tools branch sends the whole change back to dev. Acceptance: when a carried tools head (fork, client, central) is not a fast-forward, the pass rebases it onto the tools branch itself (git rebase in the change's tools worktree, no dev run) and re-records the hand-over's tools head; only a real conflict (the rebase stops) makes a dev step, naming the conflicting files; the batch ship merges every member's tools heads in one go like the harness refs; a test covers a clean rebase without a dev run and a conflicting one going to dev.

Also (filed): hd handover runs the carried tools heads' own tests
Monitor sweep 12: hd handover does not run check-tools on the carried tools heads, so harness-tools-pinned-per-process's fork commit e981c3d0e failing 2 of its own tests (BuildAttempts, ShipFailure) showed only at the batch gate (23:35), costing a batch gate plus a live gate and holding two other changes 23:32-23:37. Acceptance: hd handover runs each carried tools repo's tests (env -i, as check-tools) and refuses on a failure; a test covers it.
