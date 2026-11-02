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
- harness-qa-login-idle
- harness-up-owns-its-instance
- harness-keeper-after-failed
mechanism: desktop
created: '2026-11-01T23:59:46Z'
limit-of:
- harness-qa-login-idle
- hunter-feat-pr
---
Planner merge (planner-17) of harness-desktop-login-devtools and harness-restart-clears-disconnect-dialog. Root cause against PRD's workflow (QA proves a change on a logged-in client): the desktop login drives the screen blind, by keystrokes and fixed canvas points (tools/server/desktop_login.py offsets fixed-mode points; RuneLite's login screen has no widget ids), and ends only on LOGGED_IN, so a fast refusal hangs it (central-token-login-op-6) and the 'You were disconnected from the server' dialog, which keys do not close, stops every restart (central-login-whitelist-binds-2: the dev clicked Ok by hand). The handed-over head of harness-restart-clears-disconnect-dialog (fork c109bbaee, a fixed-point click at 382,301) must not ship: the user's word (option B) moves that work here, since a mis-aimed click on 'New User' opens a browser to Jagex.

One login path replaces those rules (the user's word: "Login was a pain point in v7, ensure our login automation is scripted and as quick as possible. Tie in with the token work to simplify the workflow, prefer devtools always."): every desktop and device logs in through the devtools login tool (client-devtools-login), fed by the issuer's compact token where the server takes token logins (harness-desktop-token-login) and by the account's password otherwise; it clears the disconnected dialog through its widget only when the devtools read it; it ends on the devtools-read outcome, LOGGED_IN or the login response code, with no fixed waits; up, restart and relogin all call it.

Acceptance: desktop_login.py's keystroke and coordinate code and the old mobile tap code are removed, with the docs/ISSUES.md entry; a refused login returns its code and exits; a restart behind the disconnected dialog ends LOGGED_IN with no manual step; proof is one server up with the desktop clients logged in and the time from client start to LOGGED_IN recorded in evidence. One test per requirement touched.

Also (moved to harness-qa-login-idle): a run's first up gets no desktop home copy after a WSL interop error
genie-review-355-134 hand-back: the first 'STAFF=1 tools/track.sh up genie-review-355' failed: instance 6 got no home copy and the log showed a WSL interop error; after down, the retry came up cleanly. Evidence: state/genie-review-355/up-134.log

Also (moved to harness-qa-login-idle): desktop_login.py token never returns once the desktop sits on a refusal screen
server-token-auth-14 hand-back (qa): 'desktop_login.py <port> token' hangs once the desktop shows a login refusal ('Incorrect username or password.'): Enter does not press 'Try again'. The run worked around it with evidence/server-token-auth/qa9-try.py. A refusal screen is a login fact: the login path presses Try again (or returns the refusal) and never waits.

Also (harness-qa-login-idle): a desktop at a login page no key leaves (a refusal's Try again, the disconnected dialog) is logged in without a hand step
harness-qa-login-idle-1 (live, token up, 2026-11-02 ~02:58Z): after a refused token the desktop shows 'Incorrect username or password.' with Try again and Forgotten password? (a Jagex link); Enter and Escape leave it unchanged, so desktop_login.py now returns 'FAILED: Enter started no login ...' instead of hanging, and the keeper stops at it until the server restarts. The disconnected dialog (server-world-entities-8, goblin qa5r) is the same: keys never close it, and a fixed-point click is ruled out (the user's option B: a mis-aimed click opens a Jagex page). The devtools expose no login page (get_client_state has gameState only), so desktop_login cannot tell or leave these pages; client-devtools-login's login-state reads and the client's own submit remove it. Pages a key does leave ('Error connecting to server', a server restart's welcome page) log back in already.
