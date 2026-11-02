---
slug: harness-tick-cost-cache
track: harness
title: 'A pass rereads only facts that changed: tick cost stays within its timer'
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T21:51:08Z'
---
Sweep 89 round 1 P2-b: hd-tick CPU 15.2s at 21:36 then 19.5, 15.4, 22.0, 24.9, 41.4, 17.4, 44.4, 21.8, 43.9, 24.4 through 21:48 (was ~10s); some passes take 70-74s wall against the 60s timer, so ticks run back to back. In the 21:48 pass hd.py had 4.5s itself and 19.6s in children (13s system, process spawns); a 50 ms sample counted 116 gh api and 91 git merge-base --is-ancestor (71 in the harness repo, one per harness change; 331 of 416 definitions are harness), plus central fetch and set-head. Each pass rereads per-change git and gh facts with subprocesses and keeps no cache across passes; cost grows with open gates and definitions. Cache facts across passes keyed on the refs they read; skip done changes. Evidence: evidence/monitor/sweep-89.md

Also (filed): A fetch forgets the pass's ref map of its clone
Sweep 89 round 4 P1-a, on harness-tick-cost-cache's head 3781b48: Facts.refs (hd.py:~120) reads every ref of a clone once per pass and rev() answers any plain ref from that map, but Facts.fetch (hd.py:~97-117) does not call forget(), so a map read before a fetch of the same clone stays stale for the rest of the pass. Ctx.tools (hd.py:~1158) reads ~/src/OpenRune-Server harness/<slug> via done -> live -> landed before the server track fetches, so every fork/dev/* and origin/HEAD the pass sees can predate the fetch: a dev pushes fork/dev/X and hands over head H, the next pass sees the old tip and lists 'dev run due: head ... not handed over' (hd.py:~1723) for nothing; a stale base skews T and gates. Tests use Fake Facts and cannot see it. fetch forgets ('refs', clone); add a test that a ref fetched after an earlier refs() read is seen. Evidence: evidence/monitor/sweep-89.md
