---
slug: harness-live-stack-issuer
track: harness
title: The live stack takes the APK's tokens from issuer.py
kind: change
priority: P1
deps:
- server-token-auth
- harness-deploy-survives-tools-ship
- harness-mobile-login-by-facts
- harness-server-stack-one-record
- harness-live-http-mount
mechanism: server
created: '2026-11-02T03:15:21Z'
---
Planner-24 split of harness-server-stack-one-deploy by root cause: its deploy acceptance (3, 5, 6) joined harness-deploy-survives-tools-ship (one deploy step keyed by tree and tools); 1 and 2 moved to harness-qa-login-idle earlier; what remains is the issuer cutover, ordered after server-token-auth. Acceptance (its 4): the live stack takes the APK's tokens from issuer.py with its DIR mounted; served jav_config params 11, 20, 22, 28 point at it; game.yml token-login holds its secret; the sidecar runs with LOCAL_AUTH false. Proof: the APK (OPENRUNE=1 LOCAL_AUTH=1) logs in on a change's stack through the issuer, contacting only local hosts. It changes a live component: before ship, hd ask the user for a yes on the cutover. Carries harness-live-issuer-cutover's tools commit 67cf143 (T 4a13623).

Also: moved to harness-relogin-inventory (relogin inventory and the STAFF list) (not blocked behind this change's deps).

Also (filed): up's second-login 'no inventory (container 93)' check fails intermittently with no server error
server-world-entities-14 (qa, head cab31a4c0): two fresh 'up 2' attempts failed at up's own 'no inventory (container 93)' check on the second login; a third identical attempt passed; the server logged nothing for either failure. up decides on a fact the client may not have reported yet, or reads the wrong desktop: find the observable fact it should wait on. Evidence: evidence/server-world-entities/in-game.md (Review server-world-entities-14), evidence/server-world-entities/qa14-server-up.log

Also (filed): The APK's login through the live stack's issuer never reaches the game server
Found by client-login-segv-osclient-5 (2026-11-02 18:43-18:54Z): three real 'track.sh up' of the live build (APK fef4307c9fc5-be9887a9ab44, modulus 8555c56c matching live tree a7fec622031537ba) passed the SIGSEGV (0 Fatal signal) and the issuer's OAuth (auth 302, token, sessions, accounts 200), then failed at a different login screen each time with nothing in osrs-openrune's log: LoginIndex 9 after Play Now, LoginIndex 3 after Play Now (issuer /game-session/v1/tokens 200), LoginIndex 39 right after the accounts fetch (mobile_login.py fails it as unknown). Evidence: evidence/client-login-segv-osclient/up-run5.md, up-run5{,b,c}.txt, up-run5c-logcat.txt. Either the game server refuses the issuer's token without a log line, or 3/39 are screens mobile_login.py must act on or wait through: find which from the app's logcat and the server's login decoder. Acceptance: a real up of the live build reaches LOGGED_IN.
