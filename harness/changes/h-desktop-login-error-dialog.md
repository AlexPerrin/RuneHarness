---
slug: h-desktop-login-error-dialog
track: harness
priority: P1
---
# desktop_login: leave the 'Incorrect username or password' dialog after a refused token (Try again), so the next login attempt starts

tracks/fork/server/desktop_login.py: after a refused token login the desktop shows the login error dialog (Try again / Forgotten password?); Enter and Escape do not leave it, so every later attempt prints 'FAILED: Enter started no login' until down. Find the dialog's component with the devtools (dump_interface / get_widget on a desktop in that state), click Try again (click_component) in attempt()/clear(), and add the case to tracks/fork/server/test_tools.py. Blocks server-android-token-login's judge (a refused forged token is one of its criteria).

## alert 16 fault 62 (×1, first 2026-11-03T12:23:15+00:00)
tracks/fork/server/desktop_login.py token: after a refused forged token the desktop sits on 'Incorrect username or password' (Try again / Forgotten password?); Enter and Escape do not leave it, so every later restart prints FAILED: Enter started no login until down
