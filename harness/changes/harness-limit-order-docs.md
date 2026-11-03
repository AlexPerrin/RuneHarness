---
slug: harness-limit-order-docs
track: harness
title: The context-limit hand-off order reads the same everywhere
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T19:45:30Z'
---
Sweep 75 P5-a: e3fe9dd/b1f1686 reordered the context-limit hand-off to stop processes before recording what was judged (qa.md:44, hook.py:633-640, docs/ARCHITECTURE.md:447), but hook.py:28 (header table) and docs/PRD.md:270 still say 'record what it judged, collect its subagents and stop its processes'. Quick doc fix. Evidence: evidence/monitor/sweep-75.md

Also (filed): Every denial event names its change and run
Sweep 76 P5-a: denial events from a run's own agent carry agent/role but no change/run (hook.py:465, 484), e.g. state/events.jsonl:10942 and 11023 (agent ad4f77e7e1702ee54 = harness-live-stack-issuer-2 per state/runs/by-agent), while other denial paths name the run; grepping events by change misses them. Evidence: evidence/monitor/sweep-76.md

Also (filed): A run may kill a background job its own command started
Sweep 77 P4-a: harness-desktop-relogin-js5-1's Monitor command 'tail -f $L | grep ... & p=$!; until ...; done; kill $p' was denied 'kill outside the run's slice: $p' (state/events.jsonl:11081, 19:53:45Z): hook.py:419-427 deny_foreign_kill accepts only digits or %n, and its text asks for a pid from the command's own output, impossible inside one command. The run dropped its process-exit check, so its watch runs to the Monitor's expiry. Allow kill of $! assigned in the same command (or %n), and state in docs that Monitor commands meet the Bash rules. Evidence: evidence/monitor/sweep-77.md
