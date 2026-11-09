---
slug: h-mobile-form-fields-filled
track: harness
priority: P1
---
# mobile_login: Central's form posted with an empty Username waits forever

Run 289, live stack 20:2x UTC 2026-11-08 (osrs-openrune without OPENRUNE_SIGN_IN_DEV_ACCOUNT), APK d77db9fa: tracks/client/track.sh up client-mobile-own-account-live reached Central's form (10.0.2.2:8084) and printed "Central's sign-in: h06df57e3cm"; sign_in() tapped the 'Username ' label and typed, tapped 'Password ' and typed, tapped Sign in. The Username EditText stayed empty, the Password EditText held the name, and Chrome's required-field tooltip 'Please fill out this field.' kept the form from posting. step() then returned 'wait' forever because the name is among the window's labels (uiautomator exposes the password field's text), so up never ended (evidence/client-mobile-own-account-live/up-a.err.txt, form-stuck.logcat.txt). Fix in mobile_login.py: type into each field's EditText (not its label), read both fields back holding the name before tapping Sign in, and judge 'posted' by the form leaving, not by the name among the labels; a form still shown after the post (a validation tooltip, a 401) is FAILED naming it. Done when two mobiles up at once (two slugs) both print LOGGED_IN through the form, and 10 consecutive ups of one slug print LOGGED_IN.

## repro: run 290 (client-probe-no-stop), 2026-11-08 20:22 and 20:59 UTC
Twice in a row on emulator-5560, APK 7399cc4f: 'Central's sign-in: h371a07328m', then the Username field empty, the Password field holding the name, 'Please fill out this field.' shown; the first up waited 34 min until Android killed the frozen app ('Async binder space running out while frozen') and printed 'FAILED: the app died' (state/client-probe-no-stop/login-failed.logcat.txt). client-probe-no-stop now depends on this change.
