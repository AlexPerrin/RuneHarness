---
slug: harness-pass-lock-followup
track: harness
title: 'Finish harness-pass-lock-short: a run''s input excludes refs its own agent
  creates; facts.jsonl compacts; one gather at a time; scopes proven from the service'
kind: change
priority: P0
deps: []
created: '2026-11-01T22:09:06Z'
---
Monitor sweep 4 (2026-11-01 22:08Z) and the fix-next answer recorded at 22:06:37Z after its handover (lost: harness answers are note rows nobody reads, harness-answer-reaches-dev). harness-pass-lock-short (8b05fb3) leaves: (a) run identity is (change, input) and the input still includes refs the run's own agent writes, so a working dev ran unbound for 19 min (agent a4cc367: pass-lock-short-1 ended 21:48:21Z when its own branch appeared; -2/-3/-4 listed for the same change while it worked, mid-rebase with UU hook.py; stop-unmatched at 22:06:16Z); (b) facts.jsonl never compacts (shortcut comment); (c) two passes fetch at once; (d) builds/gates/ships in systemd-run --scope untested from inside hd-tick.service. Acceptance: (a) one change has at most one live run, and a run's input never includes refs its own agent creates (a test: the agent creates its dev ref, the run stays and no second run is listed); (b) fold compacts facts.jsonl to the facts past the offset; (c) a second pass reuses the in-flight gather's memo or its result, never a second fetch; (d) a ship from the running hd-tick.service leaves the service cgroup (evidence from the live unit).
