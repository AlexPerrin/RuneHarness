---
slug: harness-runs-read-under-lock
track: harness
title: 'a pass reads the runs under the state lock: no run is listed twice'
kind: change
priority: P1
deps: []
created: '2026-11-01T01:49:39Z'
---
Ctx.__init__ (hd.py) loads ctx.runs = runs() before tick() takes the state lock, so a pass that waited on the lock dispatches from a stale run list: it lists a run the previous pass already listed, under the same name, overwrites state/runs/<name>.json (listed, events_at, and started/agent_id reset to None if the hook had bound it) and emits a second 'listed' event. Seen in two orchestrator windows (orchestrator-12 reported 8; now 10 of 117 runs in state/events.jsonl have more than one 'listed' event). Evidence lines:
{"action": "listed", "change": "orchestrator", "role": "orchestrator", "run": "orchestrator-13", "ts": "2026-11-01T01:44:21Z"}
{"action": "listed", "change": "orchestrator", "role": "orchestrator", "run": "orchestrator-13", "ts": "2026-11-01T01:44:28Z"}
harness-server-build-musicrepository-3 listed at 01:42:35, 01:44:08 and 01:44:27; it never started and state/runs/harness-server-build-musicrepository-3.json does not exist.
The fix reads the runs (and any other state the pass decides on) inside the lock; also find why the -3 run file is gone. One test in the R2 class (two passes, one listing).
