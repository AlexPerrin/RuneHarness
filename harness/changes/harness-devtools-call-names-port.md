---
slug: harness-devtools-call-names-port
track: harness
title: a devtools call with no port drives another run's desktop
kind: change
priority: P1
mechanism: devtools
deps: []
created: '2026-11-02T05:05:34Z'
---
server-npc-examine-without-overlay-6 (qa, desktop1:7780): at ticks 590-592 something clicked the quick-prayer orb and typed '/hi::item egg 1' in public chat on its account, and kept cancelling its walk_to calls; suspected another run's devtools calls with no port, which default to 7780 (run 1's desktop) — the cooks assistant qa (egg) was in game at the same time. A devtools call from a run must name its own desktop: the bridge refuses a call without a port (or defaults to the run's own instance), and a run is told its ports. Evidence: evidence/server-npc-examine-without-overlay/qa-6-ingame.txt
