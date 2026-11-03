---
slug: harness-join-refuses-held-target
track: harness
title: a filing joins an unrelated change and inherits its hold on the user
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T04:56:08Z'
---
sweep-38 P1-b: harness-gamevals-assign-pins (hunter-feat-pr-17's limit: tools/server/gamevals.py assign reads the pins only from $PINS, which only hd sets) was merged into harness-apk-server-rsa-key only because both are mechanism server (merge_limit hd.py:3144-3155; events.jsonl:8786); that change waits on the user's open RSA question, so the pins fix now waits on an answer about something else. A join is refused when the target is held on a question or the root causes differ; the filing becomes its own change. Move harness-gamevals-assign-pins out of harness-apk-server-rsa-key. evidence/monitor/sweep-38.md
