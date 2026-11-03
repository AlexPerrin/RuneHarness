---
slug: harness-github-reads-budget
track: harness
title: 'GitHub reads fit the API quota: one read per resource per pass, conditional,
  shared with gates'
kind: change
priority: P0
mechanism: loop
deps: []
created: '2026-11-01T22:59:21Z'
---
Monitor sweep 7: gh api rate_limit core 0/5000 at 22:56Z (reset 23:00:53Z); genie-355-bank-lamp's gate failed 'ci: tools/track.sh gate-ci' with 'HTTP 403: API rate limit exceeded' at 22:55:53Z. Every pass reads all open PRs and their comments with --paginate (two pass readers seen fetching #445's comments at once); each harness gate runs tick --dry-run three times against real GitHub (check-dry-run, track.sh:34-36); ~30 harness gates in the last hour. Root cause: GitHub reads are neither shared nor conditional, so reads grow with passes x gates. Acceptance: GitHub reads go through one cache in state/ keyed by URL with ETag/If-None-Match (304s are free), shared by passes, gates and dry-runs (a dry-run inside a gate reads the cache only, never the network); a pass reads each PR at most once; quota exhaustion is an alert and holds GitHub-dependent steps (never a head's FAIL); a test counts network reads for two passes and a gate over the same state.
