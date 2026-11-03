---
slug: harness-goal-measure-deps
track: harness
title: Client goal measures boot the emulator before the device network block exists
kind: change
priority: P0
deps: []
created: '2026-11-01T01:18:06Z'
---
hd.py measure() (hd.py:749-775) starts a goal's measure with deps [] while every client change waits on harness-device-network-block, so the client-api and client-launch measures boot an unblocked emulator and launch the client (privacy rule: no client contacts Jagex). Both died twice: state/client-api/measure.log ends 'install failed: ... INSTALL_FAILED_DUPLICATE_PACKAGE: ... Duplicate package com.jagex.oldscape.android in pending install requests', state/client-launch/measure.log ends 'FAILED: the app died'; state/client-api/proc-measure.json and state/client-launch/proc-measure.json have attempts 2. Let a goal's definition (harness/goals/<goal>.json) carry deps, and measure() wait while a dep is open, the same way next() holds a change; give client-api and client-launch the dep harness-device-network-block. One test per requirement touched.
