---
slug: harness-mobile-login-by-facts
track: harness
title: mobile_login.py never gets past the login screen
kind: change
priority: P1
mechanism: mobile
deps:
- harness-apk-server-rsa-key
created: '2026-11-02T04:22:32Z'
limit-of:
- harness-live-stack-issuer
---
sweep-34 P1-a: client-login-segv-osclient-3 (emulator-5562) and harness-live-stack-issuer-1 both stuck: the app reaches LOGIN_SCREEN, then LoginIndex 12 and 30, never LOGGED_IN; mobile_login.py ran 12-13 min and the devs fell back to adb taps (540,2084) and screenshots. state/tools/44ef4314ef38/tools/mobile_login.py:49-55: after SIGN_IN it re-taps PLAY_NOW at the fixed landscape point (1197,540) every 3 s (its own comment says a tap is never retried), never reads LoginIndex, and the fixed 2400x1080 TAPS can miss. Log in by the client's login state (LoginIndex/GameState via devtools), each step ending on the observed next state. evidence/monitor/sweep-34.md

Also (harness-live-stack-issuer): the mobile logs in to the live stack: the APK carries the live key and mobile_login drives the issuer's sign-in
From harness-live-stack-issuer-1 (evidence/harness-live-stack-issuer/proof.md). On the cutover stack the APK's issuer sign-in works (auth, token, sessions, accounts, tokens all 200) but the mobile never logs in. (1) The APK's patched RSA modulus is ~/src/openrune-work/server-tools' key (repack.sh MODULUS from scripts/openrune.sh modulus), not the live server's /app/.data/client.key (every live image's since 2026-10-31 18:32Z, carried by ship's COPY --from=live_image): the server refuses the login block with 'Invalid RSA check'. The client build takes the modulus from the live stack's key, never another repo. (2) client tools/mobile_login.py taps a LOCAL_AUTH screen: on the issuer stack the app shows New User / Existing User, then the EULA Accept, then Chrome's first run ('Use without an account') before the issuer's /oauth2/auth; it waits forever at LOGIN_SCREEN. It drives that flow on observed screens and fails (FAILED) on an unknown one. Proof: client up on live logs in (LOGGED_IN), the issuer log showing the sign-in, check-blocked passing.
