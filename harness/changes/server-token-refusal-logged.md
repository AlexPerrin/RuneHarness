---
slug: server-token-refusal-logged
track: server
title: A refused token login logs why the server refused it
kind: change
priority: P2
deps:
- server-token-auth
- harness-tree-transitive-central
created: '2026-11-02T19:41:12Z'
---
Found by harness-live-stack-issuer-2 (answer-5 of harness-live-stack-issuer, from client-login-segv-osclient-5). The APK (fef4307c9fc5-be9887a9ab44, modulus = live) signs in through the live issuer, gets the game token tester.<exp>.<mac> from /game-session/v1/tokens (logcat: 'setSSOTokenState token: tester.1793650448.Trpf...', size 61; the mac is the issuer secret's, checked), goes LOGGING_IN and 2 s later LoginIndex 3 (InvalidUsernameOrPassword) with no line in osrs-openrune's log (evidence/harness-live-stack-issuer/up-mobile2.txt, up-mobile2-logcat.txt 91228-91363). game.yml's token-login block equals issuer.py key state/live/token; a desktop token login on a change stack of the same tree (a7fec622, up 1 then RESUME=1 up token) logs in, also for an account made by password. ConnectionHandler.tokenLogin answers InvalidUsernameOrPassword with no log when TokenLoginVerifier.accountName returns null (bad shape, bad mac, expired), and the Central/AccountNotFound paths write the same code silently, so which step refuses the APK cannot be read. rsprot reads the token as a C string in the RSA block for every client type (auth type 2 only). Acceptance: every refused token login logs one line naming its cause (shape, mac, expiry, Central's code, no account) with the token's length and its account part, never the mac or the secret; the module's test covers each cause. Then the APK's live login names its refusal and harness-live-stack-issuer fixes it at that cause.
