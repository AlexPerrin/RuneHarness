---
slug: h-mobile-login-page-39-again
track: harness
priority: P0
---
# mobile start ends before LOGGED_IN: page 39 again and 'Error connecting to server' under host load

Alert 70 (fault 314). h-mobile-login-page-39 is done, yet run 314 at f8c73c3 failed twice: (1) gameState 1000 'Error connecting to server' after the launcher ANR Wait, host load 18-30, while ports 43594/8080 answered; (2) LoginIndex 39 (the client's 'Connection failed during login request' page, h-mobile-login-page-39) after Existing User and Accept. Log: evidence/client-api-probe-self-setup/up-314b.log, state/client-api-probe-self-setup/login-failed.{server,logcat}.txt. The issuer sidecar is going (h-ref-sign-in-no-issuer): find the failing request on the Central sign-in path and fix its cause, never by adding 39 to WAIT. Done when tracks/client/track.sh up <slug> prints LOGGED_IN on 10 consecutive starts, including under the load of 5 parallel runs.

## alert 70 fault 314 (×1, first 2026-11-09T03:24:47+00:00)
client up fails before LOGGED_IN twice for client-api-probe-self-setup at f8c73c3 (built from f5a4a97): (1) 22:11 ET mobile_login FAILED 'Error connecting to server' (gameState 1000) after the launcher ANR Wait, host load 18-30, server ports 43594/8080 answered; (2) 22:3x FAILED 'an unknown login screen (LoginIndex 39)' after Existing User and Accept (tracks/client/mobile_login.py WAIT={-1,30,37}, CANVAS {0,12,10}: 39 unknown). Log evidence/client-api-probe-self-setup/up-314b.log
