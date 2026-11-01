---
slug: harness-device-egress-ip
track: harness
title: The emulator block covers hostnames only
kind: change
priority: P1
deps:
- harness-device-network-block
created: '2026-11-01T01:31:50Z'
---
harness-device-network-block sets Private DNS strict to blocked.invalid, so no hostname resolves, and up checks it. Not covered: connections straight to an IP address (only 10.0.2.2 should connect), and Chrome's own secure DNS, which was not tested separately. Prove both on a device: from the emulator, a public IP (for example a Jagex or Google address) must not connect, and Chrome with secure DNS on must not load any external page. Block at the emulator's network if either gets through. Privacy rule: no client contacts Jagex or RuneScape servers. One test per requirement touched.
