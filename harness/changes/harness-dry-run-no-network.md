---
slug: harness-dry-run-no-network
track: harness
title: A dry-run pass never reaches the network, git included
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-01T23:41:41Z'
---
Monitor sweep 12: check_dry_run (tools/track.sh:36) says 'never the network', but hd tick --dry-run still runs Ctx.fetch: git fetch --prune and remote set-head --auto (hd.py:80-83); pid 1423524 ran ssh git-upload-pack to osrs-plugins-reverse inside a ship-harness gate, 3 times per harness gate, changing the live clones' remote refs from inside a gate. HD_GH=cache covers REST only. Acceptance: a dry-run (and any pass inside a gate) uses only local refs and the GitHub cache; it never fetches or writes remote refs; a test asserts no git network call in a dry-run.
