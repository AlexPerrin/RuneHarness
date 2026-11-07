---
slug: h-mobile-login-page-9
track: harness
priority: P1
deps:
- server-reconnect
---
# mobile_login: a live start ends at LoginIndex 9 (Unexpected server response) after Play Now

On the live stack (local-android-rsprot-token-gjstr and local-cs2-group-names live), run 146 ran tracks/client/track.sh up client-probe-no-stop 4 times at 08:13-08:40 UTC 2026-11-07: three ended 0 > 12 > 30 > 39 (or 0 > 12 > 39) as in h-mobile-login-page-39 (3 of 4, not 1 of 6), one ended 0 > 12 > 30 > 10 (Play Now) > 9, 'FAILED: the server refused the login (LoginIndex 9)'. The issuer logged every request 200 for that start, POST /game-session/v1/tokens at 08:20:43 included; the game server (osrs-openrune) logs no login line at all, refused or accepted, so the refusal reason is not observable: up's failure path restores the emulator before logcat can be read. Find the response code the app got on page 9 (keep logcat of a failed start in state/<slug>/, and a server-side log of login refusals with their reason) and fix its cause where it lies (server: file a fork change). Done when tracks/client/track.sh up <slug> prints LOGGED_IN on 10 consecutive starts, together with h-mobile-login-page-39.
