---
slug: h-mobile-loading-stall
track: harness
priority: P1
deps:
- h-mobile-signin-no-redirect
---
# mobile_login: a live start sits in LOADING (20%, server tick 0) after the server drops its session, and up waits on it with no end

Run 293, live stack, APK tree d77db9f, two mobiles up (client-mobile-own-account-live as h06df57e3cm stayed LOGGED_IN 21:20-22:58 UTC with taps, never lost). Ten consecutive tracks/client/track.sh up h-mobile-login-page-9 (as h49acbf16fm, each after down): starts 1 and 2 LOGGED_IN (21:30, 21:34), start 3 signed in at Central's form, Play Now 21:38:31, LOGGING_IN 21:38:35, LOADING (raw 25) 21:38:45, then 'Loading - please wait (20%)' overlay server tick 0, gameState 25, until down at 22:58 (78 min); the server logged 'Game session lost: user=h49acbf16fm' 21:40:41 and Logout 21:40:51, no refusal. mobile_login.py kept waiting on LOADING the whole time (run 211's start B mode, the same stall). Evidence: evidence/client-mobile-own-account-live/start3-stuck.png, start3-stuck.logcat.txt, ten-starts.txt, ten.server.txt. Find why the load stops at 20% and the server drops the session (server: file a fork change), and make up end on the observed fact (the session lost while the app is in LOADING is FAILED, its logcat kept), never a wait with no end. Done when tracks/client/track.sh up <slug> prints LOGGED_IN on a start while a second slug's mobile stays logged in.
