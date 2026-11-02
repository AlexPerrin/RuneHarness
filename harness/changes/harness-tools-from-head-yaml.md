---
slug: harness-tools-from-head-yaml
track: harness
title: A change's tools set comes from hd.yaml at its head, so adding a repo gates
  its tools commit
kind: change
priority: P1
deps:
- harness-filestore-track
mechanism: build-gate
created: '2026-11-02T21:51:08Z'
---
Sweep 89 round 1 P2-a: harness-filestore-track's handover (state/harness-filestore-track/handover.json) recorded tools {fork: c5a1835d} only, because ctx.tools (hd.py:1129) lists tools branches from the live checkout's hd.yaml, which lacked the filestore entry; its FileStore tools commit cef5d5b (~/src/OpenRune-FileStore harness/harness-filestore-track) was never gated (gate 0848faa65+bdf4ca47364f passed 21:38:23), ship aa3c051 put the hd.yaml filestore entry into v8 at 21:39-21:40 pointing at a FileStore local/harness still at upstream f4002f2 with no tools/track.sh, and the next pass listed harness-filestore-track-2 (21:48:12) for the grown tools set without its brief saying why. Read the repos from hd.yaml at the head (or T). Evidence: evidence/monitor/sweep-89.md
