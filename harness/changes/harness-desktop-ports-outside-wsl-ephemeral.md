---
slug: harness-desktop-ports-outside-wsl-ephemeral
track: harness
title: Desktops bind RSProx ports outside WSL's ephemeral range; up fails when the
  launcher throws
kind: change
priority: P0
deps: []
created: '2026-11-01T10:18:21Z'
---
Every server-track up fails to bring a desktop up this WSL boot (quest-runemysteries, quest-ernestthechicken, goblin-diplomacy-review-367 at 05:08-05:15 ET 2026-11-01): state/<slug>/desktopN.log ends in 'ProxyTarget.launchHttpServer ... java.net.BindException: Address already in use: bind' (RSProx HTTP on 43600+skip, proxy on 43701+skip, OsrsTestLauncher). Cause: networkingMode=mirrored in C:/Users/Alex/.wslconfig; WSL reserves the Linux ephemeral range on Windows, and this boot /proc/sys/net/ipv4/ip_local_port_range is 40525-44620, which covers 43600-43750. A Windows java bind scan of 30000-50000 showed 40525-44620 refused with no listener in netstat. Expected: up picks the desktop's RSProx ports (portskip or a base outside ip_local_port_range, checked by a Windows-side bind or the range read) so the launcher binds on any boot. Second defect: when the launcher throws, its JVM stays alive (netty threads), so desktop_start's 'kill -0' loop never ends and up hangs; up must fail with the log's exception when the log shows it (or the launcher must exit non-zero on any startup exception). One test per requirement touched.
