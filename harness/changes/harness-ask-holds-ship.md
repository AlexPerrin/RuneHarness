---
slug: harness-ask-holds-ship
track: harness
title: An open question on a change holds its gate and ship, not only its runs
kind: change
priority: P0
deps: []
created: '2026-11-01T11:08:42Z'
---
Observed: the orchestrator asked the user (hd ask) to hold harness-restart-clears-disconnect-dialog before ship (its blind click may open a browser to Jagex, the privacy rule), but an open ask only stops dispatch() from listing runs (hd.py ~863); the gate and ship scripts still ran ('gate on 19bb95ef4'). The orchestrator held it by adding a dependency on harness-desktop-login-devtools instead. Expected: while a change has an open question, the pass starts no gate, ship or upstream step for it; the answer releases it. One test per requirement touched.
