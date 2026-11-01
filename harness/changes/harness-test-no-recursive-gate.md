---
slug: harness-test-no-recursive-gate
track: harness
title: A test that drives a real gate can never run the suite that holds it
kind: change
priority: P0
deps: []
created: '2026-11-01T22:49:27Z'
---
Monitor sweep 6 (2026-11-01 22:46Z): harness-spotless-row-complete-1's uncommitted hd.py edit added the track's seed rows to contracts at read time, so the fixture contract in test_check_docs_and_gate_rows gained 'tools/track.sh check-tests'; each gate then ran the full suite, which ran that gate again (~1 level / 20 s; 47 then 82 processes, load 10.8; the orchestrator killed ~230 processes under /tmp/tmpdh923nwa and pid 3088828). The HD_E2E guard protects only EndToEnd. Root cause: a test runs a real gate whose rows can run the test suite, with no nesting guard. Acceptance: a gate run inside a test (an env marker set by the test runner) refuses to run check-tests (or any row that runs the suite) and fails loudly; the dev brief runs only the touched tests, the full suite only at the gate; a test proves a fixture contract with check-tests cannot recurse.
