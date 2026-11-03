---
slug: harness-repair-down-wrong-script
track: harness
title: The pass retries a down that cannot work, every pass, for a day
kind: change
priority: P1
mechanism: server
deps:
- harness-server-stack-one-record
created: '2026-11-02T07:47:45Z'
superseded: harness-server-stack-one-record
closed: 'answer-1: superseded by harness-server-stack-one-record'
---
Monitor sweep 55 P2-b: state/harness-staff-rights-intermittent/repair-down.json is at 1825 attempts (07:40:28Z): the change has been done since 11-01 10:17Z but its containers server-/http-harness-staff-rights-intermittent remain (Exited (255)); repairs() (hd.py:2306-2308) uses ctx.script(ch), the harness track.sh for a harness change, which has no down verb (track.sh:25 exits 2); the 'had no effect twice' alert fired once, at attempt 2. P3-a: a Created http-harness-jav-config-reland is never removed (repairs look only at server-*). Acceptance: a stack is taken down by the script that started it (or an exited/created container is removed); a repair that cannot act stops retrying and says so once.
