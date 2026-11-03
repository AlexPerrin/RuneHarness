---
slug: harness-server-stack-one-record
track: harness
title: a run's server stack is one record that up writes and every later step reads
kind: change
priority: P1
mechanism: server
limit-of:
- client-login-segv-osclient
deps: []
created: '2026-11-02T07:54:00Z'
---
Root cause (PROBLEM/PRD workflow: a run brings up its own server stack, logs its clients in, takes it down): the server mechanism does not hold a stack as one thing. up makes it (image key, containers, accounts, the script that started it), and each later step re-derives it from another source, so each diverges:
- the APK's patched RSA modulus comes from ~/src/openrune-work/server-tools while every live image since 2026-10-31 18:32Z carries another key: 'Invalid RSA check' on every APK login to live (harness-apk-server-rsa-key; client-login-segv-osclient-3: APK 8555c56c... vs live /app/.data/game.key 9FE5D348...; evidence/harness-live-stack-issuer/server-login.txt, evidence/client-login-segv-osclient/up-run3-logcat.txt);
- down takes the port from docker logs (track.sh:59-60) and loops in offline() forever once the container is gone (sweep 48 P1-b, server-clan-guest);
- repairs() takes down a harness change's stack with ctx.script(ch), the harness track.sh, which has no down verb: 1825 attempts on harness-staff-rights-intermittent's exited containers, and a Created http-* container is never removed (sweep 55 P2-b, P3-a; state/harness-staff-rights-intermittent/repair-down.json);
- STAFF names one desktop, so a run needing cheats on several accounts re-ups the whole stack per account (sweep 44 P2-a).
Fix (a rewrite of the stack's lifecycle, replacing the per-step derivations above): up writes one stack record (its containers, its RSA key pair's public modulus, its accounts and their rights, the script and repo that started it); the APK patch and every login take the modulus from it, down and the pass's repair read the containers and the script from it, and STAFF takes a list of desktops.
The second-login missing inventory (harness-relogin-inventory, the track.sh restart hang) is the server's JS5 idle close, carried by server-js5-idle-relogin; this change does not wait on it.
Acceptance: an APK built for a stack logs in to that stack (LOGGED_IN, no 'Invalid RSA check'), and up refuses to log in when the image's key and the APK's modulus differ, naming both; down ends, on an observed fact, when the record's containers are gone at any point; the pass takes a stack down with the script recorded at its up, removes an exited or created container of a done change, and a repair that cannot act stops retrying and says so once; STAFF=1,2 makes both desktops administrators in one up.
