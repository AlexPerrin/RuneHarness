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
limit-of:
- client-login-segv-osclient
superseded: harness-server-stack-one-record
closed: 'answer-3: superseded by harness-server-stack-one-record'
---
harness-live-stack-issuer-1: the live APK fef4307c (OPENRUNE=1 LOCAL_AUTH=1) signed in through the issuer (auth/token/sessions/accounts/tokens 200, twice), then the game login was refused 'Invalid RSA check': the APK's modulus is the key from ~/src/openrune-work/server-tools, while every live image since 2026-10-31 18:32Z carries a different key. So no APK can log in to live. One RSA key pair per stack: the image's private key and the APK's patched modulus come from one source, and up/ship check they match before a login. Evidence: evidence/harness-live-stack-issuer/server-login.txt, proof.md

Also (client-login-segv-osclient): The live APK cannot log in to live: its RSA modulus is not the live image's key
client-login-segv-osclient-3: the SEGV is gone on the live cache (archive 12 has no name hash 0; the app reaches LOGIN_SCREEN and LOGGING_IN with no Fatal signal), but the login block is refused 'Invalid RSA check' (osrs-openrune 04:19:38Z): the APK modulus (server-tools openrune.sh modulus, 8555c56c...) is not the live /app/.data/game.key's (9FE5D348...). Same root cause as harness-apk-server-rsa-key. Evidence: evidence/client-login-segv-osclient/up-run3-logcat.txt
