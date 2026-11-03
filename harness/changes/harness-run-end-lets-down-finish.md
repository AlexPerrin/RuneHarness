---
slug: harness-run-end-lets-down-finish
track: harness
title: A run ended by its verdict still finishes its own track.sh down
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T16:50:12Z'
---
goblin-367-rsprox-dump-15 (qa) recorded its verdict, then 'tools/track.sh down goblin-367-rsprox-dump' exited 144 as the run was ended, and the hook blocked every further command, so the stack was left up: state/goblin-367-rsprox-dump/up.json present and containers server-goblin-367-rsprox-dump and http-goblin-367-rsprox-dump running after the hand-back. Same as goblin-367-rsprox-dump-12 (up exited 144 at run end). The run's end must not kill the run's own down, or the pass must take the stack down from its record at once. Evidence: evidence/goblin-367-rsprox-dump/handoff.md
