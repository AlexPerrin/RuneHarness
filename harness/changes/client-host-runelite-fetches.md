---
slug: client-host-runelite-fetches
track: client
title: The host contacts only the local server and the two RuneLite hosts
kind: change
priority: P2
network: true
created: '2026-11-01T01:26:04Z'
deps:
- harness-mobile-network-allowlist
- client-devtools-login
---
The user's word: the client may fetch plugin data from api.runelite.net and static.runelite.net; telemetry stays blocked; no Jagex or RuneScape host ever. The head 01ab466 (NetGuard refuses every host that is not loopback or a private IPv4 literal) contradicts that. Redefine NetGuard (host/src/net/runelite/host/NetGuard.java): allow loopback, private IPv4 literals, api.runelite.net and static.runelite.net (read-only GETs, as bound in Host.java), and refuse every other host before any DNS lookup. Keep the no-retry-loop rule from 01ab466: ItemManager and WorldService fetch on success and stop on a failure. Docs (README, docs/app-telemetry.md expected hosts, docs/plugin-host.md, docs/client-state.md) state the allowed set: 10.0.2.2, api.runelite.net, static.runelite.net. The network-qa skill is changed by harness-network-qa-skill, not here. Device proof (after harness-mobile-network-allowlist): item prices and worlds load from api.runelite.net; netqa PASS with sockets to 10.0.2.2 and the two RuneLite hosts only.
