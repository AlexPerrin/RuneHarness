---
slug: server-resumed-session-logout
track: fork
priority: P0
deps:
- server-reconnect
---
# server: a resumed session that closes leaves its player in the world; every later login of the account is refused Duplicate

On the live stack (tester on the Agent_Phone, run 218): ::drop, the connection goes READER_IDLE and the client reconnects ('Game session lost: user=tester' then 'Reconnect resumed: user=tester', 02:04:36 UTC). When that resumed session's connection then closes (the app force-stopped), the server logs 'Game session closed by the server: user=''' (the resumed session carries no username) and the player is never removed: every login of tester after it, minutes later, is 'Login refused: user='' response=Duplicate' and the app ends on LoginIndex 9. Evidence: evidence/client-devtools-upstream-main/server-duplicate-after-resume.txt. Expected (official): a disconnected player leaves the world once the logout window passes (out of combat), whatever session it was resumed on, and the account logs in again. Repro: tracks/client/track.sh up <slug>, type ::drop through devtools, wait for 'Reconnect resumed' in the server log, adb shell am force-stop com.jagex.oldscape.android, then tools/mobile_login.py <slug>: Duplicate. Done when that repro logs in again after the logout window, the resumed session's close logging the username and removing the player. Blocks client-devtools-upstream-main's network QA (its ::drop relog and restart) and its rebuild's up as tester.
