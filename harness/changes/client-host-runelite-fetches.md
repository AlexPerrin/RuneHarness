---
slug: client-host-runelite-fetches
track: client
title: The host fetches from api.runelite.net and static.runelite.net
kind: change
priority: P2
deps:
- harness-device-network-block
network: true
created: '2026-11-01T01:26:04Z'
---
Traced from harness-device-network-block (evidence/harness-device-network-block/client-up.logcat.txt: 'osrsrl-host: item prices: java.net.UnknownHostException: Unable to resolve host "api.runelite.net"' every minute on the blocked emulator). The telemetry patch (tools/patch_telemetry.py, OPENRUNE=1 LOCAL_AUTH=1) removes the Jagex app's telemetry only; these fetches are the RuneLite host's own, compiled into host.jar: ItemManager GETs api.runelite.net/runelite-1.13.1/item/prices.js (f43c2d1), WorldService GETs api.runelite.net/runelite-1.13.1/worlds.js, NPCManager and item stats read static.runelite.net. NetGuard (host/src/net/runelite/host/NetGuard.java) passes read-only GETs by design, with bases bound in Host.java:197-201. The patch does not miss them; they were allowed by the client's Network QA (tools/track.md, .claude/skills/network-qa, README). The emulator now resolves no hostname, so on the device they fail and retry. Make the host contact no runelite.net host in the OpenRune build (serve prices, worlds and static data from the local server or drop the fetch), each failing once with no retry loop, and update .claude/skills/network-qa/SKILL.md and README.md (master) to the allowed set 10.0.2.2 only.
