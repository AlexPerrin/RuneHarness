---
slug: harness-desktop-one-login-path
track: harness
title: 'One scripted login through the devtools for every client: token or password,
  the disconnected dialog by its widget, ends on the read outcome'
kind: change
priority: P1
deps:
- client-devtools-login
- harness-no-powershell
- harness-desktop-devtools-jar
mechanism: desktop
created: '2026-11-01T23:59:46Z'
---
Planner merge (planner-17) of harness-desktop-login-devtools and harness-restart-clears-disconnect-dialog. Root cause against PRD's workflow (QA proves a change on a logged-in client): the desktop login drives the screen blind, by keystrokes and fixed canvas points (tools/server/desktop_login.py offsets fixed-mode points; RuneLite's login screen has no widget ids), and ends only on LOGGED_IN, so a fast refusal hangs it (central-token-login-op-6) and the 'You were disconnected from the server' dialog, which keys do not close, stops every restart (central-login-whitelist-binds-2: the dev clicked Ok by hand). The handed-over head of harness-restart-clears-disconnect-dialog (fork c109bbaee, a fixed-point click at 382,301) must not ship: the user's word (option B) moves that work here, since a mis-aimed click on 'New User' opens a browser to Jagex.

One login path replaces those rules (the user's word: "Login was a pain point in v7, ensure our login automation is scripted and as quick as possible. Tie in with the token work to simplify the workflow, prefer devtools always."): every desktop and device logs in through the devtools login tool (client-devtools-login), fed by the issuer's compact token where the server takes token logins (harness-desktop-token-login) and by the account's password otherwise; it clears the disconnected dialog through its widget only when the devtools read it; it ends on the devtools-read outcome, LOGGED_IN or the login response code, with no fixed waits; up, restart and relogin all call it.

Acceptance: desktop_login.py's keystroke and coordinate code and the old mobile tap code are removed, with the docs/ISSUES.md entry; a refused login returns its code and exits; a restart behind the disconnected dialog ends LOGGED_IN with no manual step; proof is one server up with the desktop clients logged in and the time from client start to LOGGED_IN recorded in evidence. One test per requirement touched.

Also (filed): a run's first up gets no desktop home copy after a WSL interop error
genie-review-355-134 hand-back: the first 'STAFF=1 tools/track.sh up genie-review-355' failed: instance 6 got no home copy and the log showed a WSL interop error; after down, the retry came up cleanly. Evidence: state/genie-review-355/up-134.log
