---
slug: harness-desktops-under-load
track: harness
title: Desktop sessions survive a loaded host
kind: change
priority: P1
deps: []
created: '2026-11-01T07:25:54Z'
---
Runs lose desktops when the host is busy with other runs' gates and desktops: quest-sheepshearer-3 (a devtools call hung 30 minutes, then the session dropped to the login screen and its restart login hung), goblin-diplomacy-review-367-fftgsrq-10 (desktop disconnected after ~7 minutes with no server log line, host heavily loaded; the restart login hung), server-friends-chat-clan-channels-12 (desktop 3 never opened its devtools port on a 3-desktop up). The no-cap rule stands (every run its own clients); expected: find the observable cause (host CPU/memory, the Windows side, RSProx, the devtools bridge) from these runs' logs, and make a dropped session and a devtools call that never returns end on a fact the run can act on (the session's state read back, a reconnect) instead of hanging. One test per requirement touched.
