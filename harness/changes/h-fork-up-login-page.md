---
slug: h-fork-up-login-page
track: harness
priority: P2
---
# fork track.sh up fails with desktop_login: Enter started no login, the login screen sits on a page Enter does not submit



## alert 54 fault 179 (×1, first 2026-11-07T20:08:59+00:00)
fork track.sh up <slug> 1 fails twice (20:05, 20:10 UTC) with desktop_login 'FAILED: Enter started no login: the login screen is on a page Enter does not submit and Escape does not leave'; the server log has no login attempt. Run 175's up of the same head passed at 19:43 UTC; between them harness commit 5704a0d added desktop_start's preferences.dat write ('a fresh home starts past the terms page'), the likely cause: the login screen no longer reaches the form by Escape+Enter. Logs: state/live-session-drops-after-login/qa179-up.log, qa179-up2.log, failed-up.log, failed-up-client.log. Blocks every desktop up, so no judge of an in-game criterion.
