---
slug: harness-background-wait-one-rule
track: harness
title: The roles and the hook give one rule for a backgrounded wait
kind: change
priority: P1
mechanism: roles
deps: []
created: '2026-11-02T21:00:57Z'
---
Sweep 84 P3-a: d297d90 (harness-roles-180s-background) tells runs a step backgrounded at 180 s 'is waited on by its task notification, never TaskStop it or issue it again' (dev.md:30,33; qa.md:13,16; hook.py:498,512), but end_run (hook.py:352-363) refuses a turn end while a background command runs and says 'block on it in the foreground with one until-loop', and hold_handback (hook.py:219) says 'a background command or monitor: TaskStop it'. A run following the new text is idle-refused and told to reissue the wait: the churn sweep 83 P4 described. Make the hook let a run end its turn while it waits on a background task's notification, or give the roles the hook's rule. Evidence: evidence/monitor/sweep-84.md
