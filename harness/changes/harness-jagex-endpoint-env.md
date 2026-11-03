---
slug: harness-jagex-endpoint-env
track: harness
title: One environment variable points every Jagex endpoint at our server
kind: change
priority: P0
deps:
- harness-issuer-official-shapes
created: '2026-11-01T11:41:45Z'
---
The user's word (2026-11-01): "inject an environment variable to replace jagex references with our own server endpoint". Today the Jagex hosts the clients would contact (auth/OIDC, game-session tokens, jav_config params 11 and 22, world list) are replaced piecemeal: the APK by the telemetry patch with OPENRUNE=1 LOCAL_AUTH=1, the desktops by up rewriting jav_config. Expected: one variable (e.g. OPENRUNE_ENDPOINT=<scheme://host:port>) that the APK build, the desktop launcher and up/token read, so every Jagex reference resolves to our issuer and server, with no Jagex host left reachable from any client (Privacy rule) and the official request and response shapes kept (harness-issuer-official-shapes). Proof: with the variable set, a capture of a mobile and a desktop login shows no request to a Jagex or RuneScape host and the login completes against our server. One test per requirement touched.
