---
slug: harness-listed-run-not-dropped
track: harness
title: A listed run is never dropped by the tier hold, and the hook binds runs under
  the state lock
kind: change
priority: P1
deps: []
created: '2026-11-01T21:17:41Z'
---
Found by the read-only monitor sweep (2026-11-01 ~21:12Z) the user asked for. genie-review-355 was listed and dropped 120 times 16:50-18:55Z ('held below P0/P1'); after f40e944 it still happens when a higher change appears (client-down-stops-mobile-login-5 listed 19:58:48 dropped 19:58:58; goblin-367-rsprox-dump-1 listed 20:44:56 dropped 20:45:14). harness-drop-hd-user-alert-2 was spawned at the same moment it was dropped: ended 18:31:20, started 18:31:25, record false, so its agent ran untracked outside the agent count. Cause: the drop at hd.py:1471 uses held (tier hold included); hook.py bind() (79-95) saves the run without hd's lock. Acceptance: only the hd.yaml hold band drops a listed unstarted run; bind() takes hd.lock(); tests cover a higher change appearing after a listing and a bind racing a pass.
