---
slug: harness-carry-outdated-in-one-place
track: harness
title: An alive carry on an outdated hd.py is stopped and rerun by the pass
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T19:33:34Z'
---
Sweep 73 P1-a: harness-ci-latest-run-per-check shipped 519995f (19:27:32-19:28:33Z), but the #448 carry pid 2623722 (hd.py ship server-cache-clientscript-name-hash 8c6d9679e) was still alive at 19:32Z (1h19m), hd.py mtime 14:27:32 -0500 newer than state/server-cache-clientscript-name-hash/proc-ship.json 13:18:08 -0500, no 'stopped ship' at the 19:28:33Z and 19:30:43Z passes; ship.log last 18:18:22Z 'CI wait: failure: build & boot …125055973126'. ship_step (hd.py:1875-1876) returns step('carrying upstream', ...) for an alive carry before start() is called, so d2be505's branch (key None and newer(args[0]) -> stop and rerun) is unreachable; R5 (test_hd.py +1578-1583) calls ctx.start directly. Decide outdatedness in one place (ship_step falls through to start, or start decides), with a test that drives the pass with an alive carry and a newer hd.py; the hung #448 carry then resumes (its reopen is spent). Restarts are safe (push skipped at the same head, PR found by branch, comment deduplicated by its hd:head marker, ready only while draft). Evidence: evidence/monitor/sweep-73.md
