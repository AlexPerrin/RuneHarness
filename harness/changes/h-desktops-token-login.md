---
slug: h-desktops-token-login
track: harness
priority: P1
deps:
- central-game-session
- central-sign-in-first-account
- h-live-central-sign-in
---
# Every desktop logs in by token through Central: the typed login script goes

Once central-game-session lands: tracks/fork/track.sh up and live-desktop use the token path (today only 'up token') against Central's endpoints instead of token-<slug> and issuer.py, and desktop_login.py loses the form path: no Escape, Enter, clear, typing, Tab. Only the terms page's Accept (a fresh home) and Play remain, each acting on the page it reads. A fresh C:\osrs-test's first desktop reaches LOGGED_IN. Why: on a rebuilt template the typed path fails after Accept (fields end empty; the same keys by hand log in in 4 s), and scripted typing is the fragile part of every judge's bring-up.
