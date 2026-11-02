---
slug: harness-apk-server-rsa-key
track: harness
title: the APK's RSA modulus differs from every live image's key since 2026-10-31
  18:32Z
kind: change
priority: P1
mechanism: server
deps: []
created: '2026-11-02T04:26:25Z'
---
harness-live-stack-issuer-1: the live APK fef4307c (OPENRUNE=1 LOCAL_AUTH=1) signed in through the issuer (auth/token/sessions/accounts/tokens 200, twice), then the game login was refused 'Invalid RSA check': the APK's modulus is the key from ~/src/openrune-work/server-tools, while every live image since 2026-10-31 18:32Z carries a different key. So no APK can log in to live. One RSA key pair per stack: the image's private key and the APK's patched modulus come from one source, and up/ship check they match before a login. Evidence: evidence/harness-live-stack-issuer/server-login.txt, proof.md
