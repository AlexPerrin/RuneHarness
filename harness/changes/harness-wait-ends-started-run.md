---
slug: harness-wait-ends-started-run
track: harness
title: a started run keeps running after its change starts to wait
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T04:49:15Z'
---
sweep-37 P2-a: harness-runs-view-not-pass ends a started run only when its change's next step belongs to the other role; a 'wait' step (a dep, or an open question on a dep) ends neither a started run nor a listing made by the dep action. harness-mobile-login-by-facts-1 was listed 04:26:19Z, its dep on harness-apk-server-rsa-key added 04:26:25Z, spawned 04:26:39Z, and still ran at 04:48Z (ended=null) while its step read 'waiting on harness-apk-server-rsa-key'. A wait step ends the change's started run (the run is told and hands back what it has). evidence/monitor/sweep-37.md
