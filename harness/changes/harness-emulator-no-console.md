---
slug: harness-emulator-no-console
track: harness
title: The bash bring-up opens a console window per emulator
kind: change
priority: P2
deps: []
created: '2026-11-01T01:20:08Z'
---
Since harness-no-powershell, the client track's up starts emulator.exe through cmd.exe /c start /min, so each emulator gets its own Windows console window showing its log (the user saw them). up.ps1 started it with no window. Start the emulator with no console window: its log goes to state/<slug>/emulator.log, and closing a window must no longer be the way it stops. Keep down as the only stop. On the client's client/harness-v8. One test per requirement touched.
