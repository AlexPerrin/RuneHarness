---
slug: harness-mobile-dns-not-ics-loopback
track: harness
title: Mobile up's DNS address is a Windows loopback port that Internet Connection
  Sharing holds, so every up is refused
kind: change
priority: P1
mechanism: mobile
limit-of:
- client-login-segv-osclient
deps: []
created: '2026-11-02T03:37:22Z'
---
Seen by run client-login-segv-osclient-2 (2026-11-02 03:36Z): track.sh up client-login-segv-osclient refused before boot: 'mobile-allow does not answer DNS on the Windows loopback (nslookup api.runelite.net 127.0.0.1); Windows udp 53 held by: svchost.exe (pid 22488, SharedAccess) powershell.exe (pid 30872, N/A)'. netstat -ano -p udp: 0.0.0.0:53 pid 22488 (SharedAccess, ICS, cannot be stopped) and 127.0.0.2:53 pid 30872 (a powershell.exe 'Not Responding', started by no run of this change). up replaced mobile-allow once (created 22:36 EST) and it still did not answer. Root cause: the emulator's -dns-server is a Windows loopback udp 53 that the ICS wildcard bind starves, so the mobile network allowlist depends on a Windows service's state. This is the DNS bullet of harness-mobile-up-by-facts, filed separately because that change waits on client-login-segv-osclient (a join would be a cycle); this change carries the DNS part and harness-mobile-up-by-facts drops it. Acceptance: -dns-server is an address no Windows service holds, on which mobile-allow answers udp 53 for api.runelite.net and static.runelite.net with 10.0.2.2 and NXDOMAIN for the rest, reachable from the Windows emulator, nothing on Windows stopped or reconfigured; up's nslookup proof runs against it; check-blocked passes; a test covers the address choice; a real track.sh up client-login-segv-osclient boots past the DNS proof with ICS running.
