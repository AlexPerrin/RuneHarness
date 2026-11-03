---
slug: gate-ci-external-fetch-failure
track: harness
title: 'gate-ci: a CI run failed by an external download error is not the head''s
  failure'
kind: change
priority: P0
mechanism: build-gate
limit-of:
- goblin-367-rsprox-dump
- harness-github-reads-budget
deps: []
created: '2026-11-01T22:46:42Z'
superseded: harness-build-gate-keyed-process
closed: 'answer-5: superseded by harness-build-gate-keyed-process'
---
goblin-367-rsprox-dump's gate failed at a correct head: CI run 41357682052 on gate/goblin-367-rsprox-dump died in 'Generate cache and gameval sources' (:or-cache:freshCache) on HTTP 500 from https://archive.openrs2.org/caches/runescape/2752/disk.zip, which served 200 minutes later. tools/gate/gate.sh gate_ci reads any completed non-success run as the head failing, so the change returns to a dev run with nothing to fix. Acceptance: a gate-ci failure caused by an unavailable external source (the cache archive, a dependency host) never sends a change back to dev as its own failure: either the CI does not depend on that fetch at gate time (the cache the build copy already has) or the gate tells the infrastructure failure apart from the head's and reruns on an observed fact (the source answering), no timed retry.

Orchestrator: moved to the harness track (gate-ci is harness tooling). Root cause to address with it: the fork CI downloads the 213 MB cache from archive.openrs2.org on every gate run (see harness-live-deploy-evidence, which shares the cache for live builds); a cached copy in CI (actions/cache keyed by cache id) removes the external dependency, and a failed fetch is then reported as an infrastructure failure that re-runs, never as the head's FAIL.

It blocks #367 now: goblin-367-rsprox-dump-4 re-handed over the same head, but the failed gate stands for that head and its step stays due with no run listable (alert 2026-11-01). Acceptance adds: a CI failure in a step the head does not touch (cache/gameval generation, checkout, setup) re-runs the gate on the same head instead of failing it.

Monitor sweep 6 adds (same mechanism, cache fetch): server-cache-clientscript-name-hash gate CI (run 41357793032) failed on the same openrs2 HTTP 500; nine more gate CI runs were in flight on the same download. Every CI run and every deploy downloads the cache fresh.

Also (harness-github-reads-budget): gate-ci: CI status reads fit the GitHub quota and a quota refusal holds the row
Found by harness-github-reads-budget. tools/gate/gate.sh gate_ci (fork local/harness) polls 'gh run list' (REST core) every 30 s per workflow per gate in flight, unconditionally, so concurrent gates drain the 5000/h core quota; on a 403 rate-limit refusal the row fails (genie-355-bank-lamp's gate failed 'HTTP 403: API rate limit exceeded' at 22:55:53Z), a head's FAIL for an infrastructure fact. hd now keeps one conditional cache of GitHub REST reads (state/gh/<hash>.json, If-None-Match its ETag, 304s free) and state/gh/quota.json {reset} while GitHub refuses on quota. Acceptance: gate_ci reads its run status conditionally (through that cache, e.g. repos/<fork>/actions/runs?branch=gate/<slug>&head_sha=<sha> with If-None-Match), and a quota refusal leaves the row held (no result recorded, re-run once GitHub's reset passes), never a failed gate.
