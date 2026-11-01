---
slug: harness-mobile-allow-ports
track: harness
title: 'up: mobile-allow''s ports reach the Windows loopback (the mobile resolves
  through it)'
kind: change
priority: P1
deps: []
created: '2026-11-01T19:43:17Z'
---
From client-down-stops-mobile-login run 2 (2026-11-01 ~19:40Z): track.sh up fails in check-blocked with 'NOT REACHED: api.runelite.net static.runelite.net' ('nc: api.runelite.net:443: No address associated with hostname' on the mobile). The container mobile-allow is running (docker run -p 127.0.0.1:53:53/udp -p 127.0.0.1:443:443) and answers inside it (nslookup api.runelite.net 127.0.0.1 in the container gives 10.0.2.2), but from Windows nslookup.exe api.runelite.net 127.0.0.1 gets no response, and netstat.exe shows no listener on 127.0.0.1:53 or 127.0.0.1:443; UDP 0.0.0.0:53 is held by svchost (SharedAccess, Internet Connection Sharing). The allowlist proved itself at 00:05 EDT the same day (evidence/harness-mobile-network-allowlist/check-blocked.txt). The dev run's 'docker stop mobile-allow' + re-run was denied by the permission classifier, so whether a restart restores the publish is unproven. Fix in tools/track.sh boot (client tools branch client/harness-v8): up proves the container's ports answer on the Windows loopback (a DNS query for api.runelite.net through nslookup.exe or equivalent) before booting, and when they do not, restarts or replaces the container it can own, or fails naming the holder of the port (e.g. SharedAccess on udp 53). Proof: a fresh up passes check-blocked. One test in tools/test_track.py.
