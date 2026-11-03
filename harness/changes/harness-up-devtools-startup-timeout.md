---
slug: harness-up-devtools-startup-timeout
track: harness
title: up waits for the desktop's devtools endpoint to answer before its first key
  or typing call
kind: change
priority: P1
deps: []
created: '2026-11-01T14:00:00Z'
---
Hand-back of harness-up-inventory-widget-empty-1 (2026-11-01): one RESUME=1 up stopped with 'FAILED: devtools endpoint on 7780: <urlopen error timed out>': a key or typing call timed out while the client was still starting. Running up again worked. Non-blocking (a rerun works) but costs a run an up. Acceptance: up's first key or typing call goes only after the endpoint has answered a request (an observed fact, not a timer); a test covers a slow-starting endpoint.
