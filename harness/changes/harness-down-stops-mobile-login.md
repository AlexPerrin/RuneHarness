---
slug: harness-down-stops-mobile-login
track: harness
title: track.sh down stops the run's mobile_login.py
kind: change
priority: P2
deps: []
created: '2026-11-01T04:13:36Z'
---
From client-down-stops-mobile-login: the fix is in tools/track.sh and tools/mobile_login.py on the client tools branch client/harness-v8 (master has no tools/track.sh, so a client-track run cannot make it). up runs mobile_login.py in the foreground; when up's caller dies (a killed or backgrounded shell) mobile_login.py outlives it, and after down's 'emu kill' it keeps polling adb (its loop returns only when the app was once seen alive, and adb on an offline serial can block). Fix: up writes the login's pid to state/<slug>/login.pid (run it as a child, record $!, wait on it); down kills that pid (and its children) before 'emu kill' and removes the file. Proof: after down, no mobile_login.py with that run's ANDROID_SERIAL is alive (ps). One test in tools/test_track.py: a stub mobile_login.py that sleeps, up interrupted, down leaves no stub process.
