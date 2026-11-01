---
slug: harness-device-network-block
track: harness
title: The emulator can reach Jagex and RuneLite hosts
kind: change
priority: P0
deps: []
created: '2026-11-01T01:10:05Z'
---
Privacy rule: no client ever contacts Jagex or RuneScape servers. In the harness-no-powershell-2 proof run, a device_login tap opened Chrome on https://legal.jagex.com/docs/policies/privacy (logcat recorded it as the captured link), and the app's host fetched item prices from api.runelite.net. Nothing on the emulator blocks those hosts. Block them on the device side for every emulator the client track boots (for example a hosts file or a DNS that answers only local hosts, set in up), and make up verify it with a check that fails if any Jagex, RuneScape, RuneLite or Google host resolves or connects. Also trace why the telemetry-patched APK's host still fetches from api.runelite.net, and file that as a client change if the patch misses it. Evidence: evidence/harness-no-powershell/proof.md (harness-no-powershell-2). One test per requirement touched.
