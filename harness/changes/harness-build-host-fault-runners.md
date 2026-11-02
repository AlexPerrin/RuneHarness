---
slug: harness-build-host-fault-runners
track: harness
title: a host fault (OOM) is recorded as the head's build FAIL; concurrent builds
  are unbounded
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T01:54:07Z'
---
sweep-18 N7, lost by sweep-19 N10: quest-runemysteries build e302c87c5-0f917e5975f1 01:38:52Z: gradle BUILD SUCCESSFUL, docker build 'cannot allocate memory' -> 'build failed: dev' (hd.py:1422-1423). build.sh:47/61/65 records every docker failure with 'record false build'. The c5f8946e0 ship moved every build key; start() launched 12 builds at 01:36:32Z, each --cpus=4 --memory=5g on 16 CPU / 19 GB (load 35, free 0); build.lock is per slug. A host fault is the runner's (re-run), and concurrent builds are bounded by the host. evidence/monitor/sweep-18.md, sweep-19.md

Also (filed): every row key hashes all of tools/gate/, so a gate.sh change re-runs every server CI
sweep-19 N11: Ctx.key each=True hashes tools_run(files, 'tools/gate/', cmds) for every row; the fork's tools/gate holds only gate.sh, so a gate.sh change (c5f8946e0) moves every row's key, the CI row's included (sweep-18 N8). Key each row on the gate.sh parts it runs, or keep the CI row's result when only its unrelated parts moved. evidence/monitor/sweep-19.md
