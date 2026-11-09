---
slug: h-mobile-login-pages
track: harness
priority: P1
---
# mobile_login: the mobile sign-in fails on LoginIndex 39 and 3 (and 9) after Play Now; up never logs in

tracks/client/track.sh up <slug> fails at sign-in on every start this run: twice on the change client-probe-no-stop at 2026-11-03 00:4x ET (APK 2f3e35ed, the live modulus, allowlist checked): LoginIndex 0 Existing User, 12 Accept, 30 Chrome 'Use without an account', 10 Play Now, then FAILED: an unknown login screen (LoginIndex 39), then (LoginIndex 3) on the retry. state/client-api/measure-fef4307c9fc5.log shows the same three outcomes on the live APK (39 before Play Now, 3 after, then 9 the server refusing it). The live server log (tracks/fork/track.sh log live) shows no login line at those times. Find what pages 3 and 39 are (screenshot and the host's log at that moment, client-state.md's Login screen pages table) and the root cause: a transient page the tool should wait through, or a refusal from the game server or the issuer (then a fork change with the repro). Done when up <slug> prints LOGGED_IN on consecutive starts. Without it no client change can produce a mobile api-probe report (check-probe needs the host.jar build line, which the desktop fallback lacks) or mobile evidence.
