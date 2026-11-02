---
slug: harness-build-gate-keyed-process
track: harness
title: 'A build, gate or deploy is a process of its key: keyed on what it runs, run
  from that key''s files, replaced when the key moves, failed only by the head'
kind: change
priority: P0
mechanism: build-gate
deps: []
created: '2026-11-01T23:59:46Z'
---
Planner merge (planner-17) of harness-build-key-and-stale-gates, harness-tools-pinned-per-process and gate-ci-external-fetch-failure, which patch one mechanism. Root cause against PRD's workflow (a complete PR is gated, then carried): a build, gate or deploy is not a function of its key. Its key hashes files it never runs (tools/gate/gate.sh holds build and gate-ci code: a gate-ci edit rebuilt all 10 server changes at 23:24:49 and 23:30:57; server-world-entities has 33 build logs for tree 1fc56bf); it executes from the tools worktree a ship mutates (deploy attempt 2, ee13b4c, failed 'open Dockerfile: no such file' at 22:35:22 after a 22:27 tools ship moved the file); a process whose key moved keeps running because ctx.start (hd.py:825) matches on name alone (10 gate-ci pollers on the old loop after 23:30:28; pid 1045784 ran 17+ min while its new build pid 1219113 waited on build.lock), and the state names a key other than the running one (hd.py:1319); its result is read as the head's even when the failing step is outside the head (openrs2 HTTP 500 on :or-cache:freshCache, CI runs 41357682052 and 41357793032; 'HTTP 403: API rate limit exceeded' on genie-355-bank-lamp at 22:55:53Z); a carried tools head that stopped fast-forwarding sends the change to a dev run that only rebases (harness-tools-pinned-per-process took four); hd handover does not run the carried tools heads' tests (fork e981c3d0e failed BuildAttempts and ShipFailure only at the batch gate, 23:35).

One mechanism replaces those rules: a build/gate/deploy process is keyed on exactly the files it runs, runs from a read-only checkout of those files at its key, is the only process holding proc-<role> for its scope and is replaced when its key moves, and records a failure as the head's only when the failing step reads the head.

Acceptance (each with a test):
- build and gate code are separate files with separate keys; a gate-ci or gradle-volume edit never rekeys a build.
- each build/gate/deploy runs from a per-key read-only checkout of the tools (worktree or archive); a tools ship while a fake deploy runs leaves its files unchanged.
- a running build/gate/ship whose key is no longer current is stopped (its scope) and the current one started; the state names the key of the process actually holding proc-<role>, so a multi-member batch gates the batch it names.
- the fork CI does not fetch the cache from archive.openrs2.org at gate time (actions/cache keyed by cache id, the copy live builds already share); a failure in a step the head does not touch (cache/gameval generation, checkout, setup) or a GitHub quota refusal records no result and re-runs on the observed fact (the source answering, the quota reset), never a timed retry and never a FAIL of the head.
- gate_ci reads run status conditionally through hd's GitHub cache (state/gh, If-None-Match, quota.json).
- a carried tools head that is not a fast-forward is rebased by the pass in the change's tools worktree (no dev run) and the hand-over's tools head re-recorded; a stopped rebase makes a dev step naming the conflicting files; the batch ship merges every member's tools heads at once.
- hd handover runs each carried tools repo's tests (env -i, as check-tools) and refuses on a failure.
