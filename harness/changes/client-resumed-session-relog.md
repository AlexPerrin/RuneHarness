---
slug: client-resumed-session-relog
track: client
priority: P1
deps:
- server-resumed-session-logout
---
# client: after a ::drop reconnect and a force-stop, the app logs tester in again on the live stack

Checks server-resumed-session-logout once it runs live, the definition's own repro on the Agent_Phone: tracks/client/track.sh up <slug>, ::drop through devtools, wait for 'Reconnect resumed: user=tester' in the live server log, adb shell am force-stop com.jagex.oldscape.android, then tools/mobile_login.py <slug>. Done when the server log shows 'Game session lost: user=tester' (or 'closed by the server: user=tester') for the resumed session, the player removed after the logout window, and the login succeeds (no response=Duplicate, the app LOGGED_IN, not LoginIndex 9). Evidence beside evidence/client-devtools-upstream-main/server-duplicate-after-resume.txt.
