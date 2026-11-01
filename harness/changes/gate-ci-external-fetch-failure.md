---
slug: gate-ci-external-fetch-failure
track: harness
title: 'gate-ci: a CI run failed by an external download error is not the head''s
  failure'
kind: change
priority: P2
mechanism: gate-ci
limit-of:
- goblin-367-rsprox-dump
deps: []
created: '2026-11-01T22:46:42Z'
---
goblin-367-rsprox-dump's gate failed at a correct head: CI run 41357682052 on gate/goblin-367-rsprox-dump died in 'Generate cache and gameval sources' (:or-cache:freshCache) on HTTP 500 from https://archive.openrs2.org/caches/runescape/2752/disk.zip, which served 200 minutes later. tools/gate/gate.sh gate_ci reads any completed non-success run as the head failing, so the change returns to a dev run with nothing to fix. Acceptance: a gate-ci failure caused by an unavailable external source (the cache archive, a dependency host) never sends a change back to dev as its own failure: either the CI does not depend on that fetch at gate time (the cache the build copy already has) or the gate tells the infrastructure failure apart from the head's and reruns on an observed fact (the source answering), no timed retry.

Orchestrator: moved to the harness track (gate-ci is harness tooling). Root cause to address with it: the fork CI downloads the 213 MB cache from archive.openrs2.org on every gate run (see harness-live-deploy-evidence, which shares the cache for live builds); a cached copy in CI (actions/cache keyed by cache id) removes the external dependency, and a failed fetch is then reported as an infrastructure failure that re-runs, never as the head's FAIL.
