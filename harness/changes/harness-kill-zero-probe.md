---
slug: harness-kill-zero-probe
track: harness
title: A kill -0 liveness probe is not a kill
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T20:38:31Z'
---
Sweep 82 P4: deny_foreign_kill (hook.py:429-441) treats kill -0 as a kill: harness-text-rows-keyed-on-texts-3 ran 'p=$(pgrep -f ...); while [ -n "$p" ] && kill -0 $p; do sleep 5; done' and was denied at 20:31:20Z (state/events.jsonl:11239); it worked around by typing the pid. kill -0 sends no signal: exempt it. Evidence: evidence/monitor/sweep-82.md
