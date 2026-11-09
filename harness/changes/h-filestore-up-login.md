---
slug: h-filestore-up-login
track: harness
priority: P2
deps:
- h-desktops-token-login
- server-token-auth
---
# filestore track's up: its desktop logs in to the server built on upstream main

tracks/filestore/track.sh up <slug> 1 builds the fork's base (OpenRune-Server origin/main, i.e. upstream) with the FileStore head and starts it, but its desktop never logs in, so no FileStore change can show a client logged in (filestore-cs2-group-name-hash's proof: 45550 and 45553 at login, ::spawn opening the spawner). Observed 2026-11-06 twice: up 1 -> 'FAILED: Enter started no login: the login screen is on a page Enter does not submit and neither Escape nor Try again leaves (the disconnected dialog)'; desktop1.log shows JS5 served (master index) and no login packet sent, so the client never submits the form (the typed-path failure h-desktops-token-login names). up token -> 'FAILED: back at the login screen: the server refused the token' (server: INVALID_LOGIN_PACKET), since upstream main has no token login. h-desktops-token-login moves desktops to Central's token login, which a server on upstream main does not accept either: the filestore up needs a base its desktop can log in to (the fork's main with token auth, or a working form path). Done when tracks/filestore/track.sh up filestore-cs2-group-name-hash 1 reaches LOGGED_IN.
