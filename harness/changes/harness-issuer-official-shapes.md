---
slug: harness-issuer-official-shapes
track: harness
title: issuer.py serves the APK's OIDC and the official game-session shapes
kind: change
priority: P0
deps: []
created: '2026-11-01T11:39:06Z'
---
From harness-token-issuer-long-term (evidence/harness-token-issuer-long-term/plan.md): one carried issuer for test and live. On the fork's local/harness, tools/server/issuer.py takes over the v7 sidecar's auth part (local/server-tools sidecar LocalAuth.kt): the OIDC endpoints the APK's AppAuth uses (.well-known/openid-configuration, oauth2/auth, oauth2/token, userinfo, jwks), and game-session with the shapes RSProx records. These are: POST sessions takes {idToken} and answers {sessionId}; GET accounts checks Authorization: Bearer <sessionId> and answers [{accountId:Int, displayName, userHash:Long}]; tokens answers {token} (JSON, which the desktop client is observed to parse). The account the APK signs in as is a file in the issuer's DIR, like token. It listens on https (the desktop trusts tls.pem) and on http (the APK's LOCAL_AUTH allows cleartext), so the client needs no change. Tests in tools/server/test_tools.py. No live component changes here.
