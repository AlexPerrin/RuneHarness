---
slug: harness-pin-conflict-run-held
track: harness
title: a held change's pin-conflict step lists no run
kind: change
priority: P0
deps: []
created: '2026-11-01T18:49:56Z'
---
The pin-conflict branch of ship_test (hd.py ~line 938) calls dispatch() directly, outside the tier-hold check at line 1284 (`elif st["actor"] in ("dev", "qa") and not held: dispatch(...)`). Each pass lists a run for the held change, and the end-of-pass loop ends it unstarted with "held below P0": a run file, a brief and a listed event per pass, forever.
Evidence (state/events.jsonl, state/runs/):
- {"action": "listed", "change": "genie-review-355", "role": "dev", "run": "genie-review-355-10", "ts": "2026-11-01T16:50:52Z"} ... through genie-review-355-122 at 2026-11-01T18:48:36Z, every 10-40 s; 7 started runs ever, 122 run files.
- state/runs/genie-review-355-119.json: started None, reason "held below P0", step "pin content/looting-bag conflicts with the integration tree (content/genie, feat/hunter, content/pirates-treasure): dev".
Fix: the tier hold applies to every dispatch (one check, in dispatch or its one caller path), so a held change lists no run on any step. Proof: a test where a held change with a pin-conflict step lists no run across two passes; then no genie-review-355-N is listed while it is held.
