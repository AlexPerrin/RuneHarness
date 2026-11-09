---
slug: h-mobile-token-login
track: harness
priority: P1
---
# the mobile starts signed in: a Central session for the slug's account seeded before the app's start, Play Now its one tap

The user's word (2026-11-09): on BlueStacks the tester was preloaded and login was one click; pass the credentials before the start. Today each start runs Existing User, Accept, Chrome's first run (24 s, evidence/home-nudge/logcat-start.txt), Central's form typed field by field, the redirect, then Play Now. The desktops already start from a Central token with only Accept and Play (h-desktops-token-login, desktop_login.py token).
Needed: tracks/client/track.sh up mints the slug's own account's session from embedded Central (the token path the desktops use; the account name mobile_login.account(), never shared: a second login of one account is refused Duplicate) and seeds it where the app reads a saved sign-in, with the terms accepted, in the same step that pushes the plugins, before the app's one start; mobile_login then acts on Play Now alone. First find how the app keeps its AppAuth state: plain app data (written by adb root on a no-Play image, or by run-as with debuggable set by the LOCAL_AUTH repack), or bound to the device keystore (then the LOCAL_AUTH repack reads a pushed token file instead of AppAuth, like the desktops' session variables). The browser sign-in at Central's form stays proved: H8's evidence, and a scripted criterion of the changes that touch sign-in, not a step of every up. Privacy unchanged: only Central on the stack is asked, OPENRUNE=1 LOCAL_AUTH=1, javcheck passes.
Done when: tracks/client/track.sh up <slug> reaches LOGGED_IN with Play Now as its only tap and no Chrome activity started (logcat), on 10 consecutive starts, and the boot-to-LOGGED_IN time is recorded against today's (evidence/h-mobile-token-login/).
