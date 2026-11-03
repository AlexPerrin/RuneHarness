---
slug: harness-desktop-first-login
track: harness
title: The first desktop login on a fresh server database fails
kind: change
priority: P1
deps: []
created: '2026-11-01T02:19:57Z'
---
genie-review-355-6 reported: on a fresh database, track.sh up fails at the first login ('back at the login screen'); logging in again works. The user saw a desktop client show 'You were disconnected from the server.' while three test servers had just restarted (2026-11-01 ~02:19Z). Also from that run: desktop_login.py relog sends ::drop, which this server does not have, so it hangs. Find why the first login on a new account drops (account creation racing the login, or the members update), make up log in once with no retry needed, and remove ::drop from relog. One test per requirement touched.
