---
slug: client-login-segv-osclient
track: client
title: The app dies with SIGSEGV in osclient.so (via a libosrsrl hook) before the
  login
kind: change
priority: P2
deps:
- server-cache-clientscript-name-hash
- harness-mobile-dns-not-ics-loopback
- harness-mobile-login-by-facts
- harness-server-stack-one-record
created: '2026-11-01T20:17:21Z'
---
Seen in a real 'track.sh up' from run harness-mobile-dns-off-loopback-1 (2026-11-01 ~19:12Z, APK T fef4307c9fc5, the live build) on the network allowlist, after check-blocked passed. mobile_login.py reports 'FAILED: the app died'. Logcat: evidence/harness-mobile-dns-off-loopback/up2-logcat.txt. At 15:12:45 local time the game thread osrsrl-game (tid 4851) took Fatal signal 11 SEGV_MAPERR at fault addr 0x0 (a null read). Backtrace: #00 pc 4160ec and #01 pc 411b34 in liblibs.hal.system.osclient.so, #02 pc 83a6f0 in libosrsrl.so (BuildId db6ef79e62fa), #03 pc 73bf30 in osclient.so. The app runs arm64 under Berberis on the x86_64 Agent_Phone. The game was still at the login stage (GameStateChanged UNKNOWN). Varps went from 0 to 65660 at 15:12:37, then the game thread was silent for 8 s. The app did reach the network: 'item prices: 4693 from api.runelite.net'. No DNS errors from the app. It reproduced twice in a row; evidence/harness-no-powershell/client-up.log shows the same 'the app died'. Acceptance: a real up of the live build reaches LOGGED_IN.
