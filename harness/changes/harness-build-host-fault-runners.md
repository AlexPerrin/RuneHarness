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

Also (filed): a failing test's reason never reaches the gate record
sweep-21: tools/track.sh:30 summary() keeps only 'Ran/OK/FAILED/FAIL: name' lines, so the assertion and traceback are dropped; dev briefs get only the test name (state/briefs/harness-late-answer-from-run-start-2.md:11-14). EndToEnd.test_harness_change_defined_to_live failed on two unrelated changes (198599b8d 02:00:37Z, 49fe4278a 02:03:26Z) while the base passed twice (23 s, 33 s vs 40 s, 55 s under 3 concurrent gates); suspect a race in its until() loop ('stuck' when no proc alive and the view equals last while a process ends between pass and glob). The gate keeps each failing test's traceback tail. Also: a ship drops the gate it just shipped (track.sh:80 rm -f gate-*.json; 987a686be re-gated 02:01:27-02:02:15Z): keep gate-$G of the shipped tree. Also: the live branch's own gate runs the member's rows under the member's slug and overwrites its row-*.json (state/harness-late-answer-from-run-start/row-gate-tests.json now holds the base's OK; hd.py:1525-1531, 2575-2582). evidence/monitor/sweep-21.md

Also (filed): a build fails on a leftover container of the same name
state/live/ship.log: the integration deploy of 58031243875c failed twice ('ship died twice without a result' alert): state/integration/build-58031243875c85136c0a901025a74669ec1bbdbd-2.log: 'docker: Error response from daemon: Conflict. The container name "/build-integration" is already in use by container 26ec0218f9a8...'. A build's container is named per slug, so one left by a stopped or killed build blocks every later build of it. A build owns its container per key/attempt and removes a leftover of its own name before it starts (a host fault, not the head's).

Also (filed): a stopped build's container keeps running: R5's stop does not reach the docker container
Root cause of the 'ship died twice without a result' alert (planner-22): events.jsonl 02:12:03Z 'stopped ship' key 6bf30c2ac635-5fb469b68a22 pid 3346773; hd.py:338 stop() ends the script's systemd scope, but the container 'build-integration' (created 02:04:33Z by tools/build/build.sh:47 docker run --name build-$slug) lives in dockerd's cgroup and keeps running (docker ps 02:15Z: Up 11 minutes, still downloading the cache; no process holds state/integration/build.lock per fuser). The ship of 58031243875c then failed twice on the name conflict (state/integration/build-58031243875c...-1.log, -2.log). R5 'a stop ends everything the script started' fails for containers: the build's container ends with its script (build.sh removes its own container on exit and, under build.lock which makes the name its own, removes any leftover of that name before docker run), so a stop frees the host and a later build never meets it.
