---
slug: harness-mobile-network-allowlist
track: harness
title: The mobile resolves and reaches the two RuneLite hosts, telemetry stays blocked
kind: change
priority: P0
deps: []
created: '2026-11-01T03:41:50Z'
---
The user's word: the client may contact api.runelite.net and static.runelite.net (plugin data); telemetry stays blocked; no Jagex or RuneScape host ever (CLAUDE.md privacy). harness-device-network-block (client tools bb2a798) made up set Private DNS strict to blocked.invalid, so no hostname resolves at all (tools/track.sh:95,108), and the Windows Firewall group osrs-harness blocks qemu-system-x86_64.exe and netsimd.exe from every address but loopback and the LAN (client tools/track.md:34-36); check-blocked fails if api.runelite.net resolves (tools/test_track.py:125). Replace this with an allowlist: on every mobile the client track boots, api.runelite.net and static.runelite.net resolve and connect on 443, and every Jagex, RuneScape, Braze, OneTrust, Google analytics/Firebase and Singular host, and any other public host, neither resolves nor connects (for example a host-side resolver that answers only the allowed names, given to the emulator, and firewall rules that admit the two hosts' connections only). check-blocked (run by up) proves both halves and fails on either. If Private DNS is no longer used, harness-up-private-dns-wait is moot and closes. Fix carried on client/harness-v8. One test per requirement touched.
