---
slug: harness-gate-held-row-own-stop
track: harness
title: A gate row is held only for a stop of its own process, not any run's stop
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T14:55:36Z'
---
Sweep 57 P3-a: stopped() writes one global time to state/stopped on every slice and script stop (hd.py:307, hd.py:350); hd.py:2976 holds any signal-ended gate row if any stop happened while it ran, whatever run it belonged to, so a head's JVM crash (exit >128) during another run's end records no verdict and re-runs, against e9d4d02 ('any other end, a crash among them, is the head's'). Repeated processes-ended events widen the window: quest-completion-recorded-ticks-2 ended at 14:51:00Z and 14:51:23Z; server-world-entities-9 six times 03:34-03:40Z (state/events.jsonl:8314-8352), from the cleanup loop hd.py:2532-2536. Fix at the root: tie the stop to the row's own process or slice. Evidence: evidence/monitor/sweep-57.md

Also (filed): A harness gate and ship start while Docker is down
Sweep 58 P3-a: Ctx.start returns at once when Docker is down (hd.py:1267), for every script, the harness batch gate and ship included (hd.py:1750); dockerless() (hd.py:1224-1226) already exempts harness runs, and a harness gate with tools: {} runs only check-tests, dry-run, docs and tools. Three harness heads sat at 'gate on 29c0f993a' with no gate started (events.jsonl:9851-9853; state/ship-harness/proc-gate.json still the 08:23:28Z gate). The Docker alert (hd.py:2314, 'no script starts') hides it. Evidence: evidence/monitor/sweep-58.md

Also (filed): A ship keeps a failed prefix's gate result at its key
Sweep 59 P4-d: clearing kept gate records on ship drops a failing prefix's result, which is then gated again at the same key: a5d5cbc58 gated 15:01:52Z, cleared by the 15:04:45Z ship, re-gated 15:07:34Z (~1 min each). Evidence: evidence/monitor/sweep-59.md

Also (filed): A batch member is blamed only on its own gate run, never a reused live-branch record
Sweep 60 P3-b: a flaky R2 test failed in EndToEnd's nested suite at gate 6ed850fc6+53b837c778a7+54dc32cfb385 (15:21:49Z) and harness-server-stack-one-record was blamed and sent to a dev run (15:22:14Z) without a re-run: batch() took the live-branch record gate-8ec1867cf (ok) as the member's own key bk. The test passed at the top level of the same gate and in 42 reruns. Also sweep 60 P3-c: c291e74's kept() keeps every failed gate record forever and batch() treats a kept failure as final, so such a flake would stick to its tree across ships; bound the kept failures (e.g. only while their members are still at the gated heads, or for one ship). Evidence: evidence/monitor/sweep-60.md, state/ship-harness/tests.txt
