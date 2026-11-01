---
slug: harness-mobile-dns-off-loopback
track: harness
title: The mobile's DNS reaches mobile-allow without Windows udp 53 on the loopback
kind: change
priority: P1
deps: []
created: '2026-11-01T19:58:29Z'
---
harness-mobile-allow-ports (6c8ed8d) found Windows Internet Connection Sharing (SharedAccess, svchost) holding udp 0.0.0.0:53, so DNS to 127.0.0.1:53 never reaches mobile-allow and 'track.sh up' refuses every mobile. The user tried 'Stop-Service SharedAccess' as admin (2026-11-01): 'Service Internet Connection Sharing (ICS) (SharedAccess) stop failed.' SharedAccess likely serves WSL/Hyper-V networking and must stay. The emulator's -dns-server takes an address only (no port). Seen from WSL: eth0 192.168.2.10 (looks like mirrored networking). Acceptance: the mobile's -dns-server is an address (not a Windows loopback address SharedAccess holds) on which mobile-allow answers udp 53 for the allowlisted names and refuses the rest, reachable from the Windows emulator; nothing on Windows is stopped or reconfigured; up's existing proof (nslookup expects 10.0.2.2) runs against that address; a test covers the address choice; a real up reaches the login.
