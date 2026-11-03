---
slug: harness-ship-pass-ends
track: harness
title: the pass that ships the harness goes on under the old code and starts builds
  that are killed right after
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T01:19:37Z'
---
sweep-16 N3: at 01:08:39Z the shipping pass started 12 builds with no key ('building 286823c78', logs -ed06703a4fa0-1); at 01:09:25Z all 12 were 'stopped build key null' and restarted as -d52722213 (~46 s x 12 builds wasted). The running pass keeps the hd.py and tools it loaded before the ship: a pass that ships the harness ends after the ship. evidence/monitor/sweep-16.md
