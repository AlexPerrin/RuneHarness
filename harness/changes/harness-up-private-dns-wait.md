---
slug: harness-up-private-dns-wait
track: harness
title: up's Private DNS wait ends on a fact
kind: change
priority: P1
deps:
- harness-device-network-block
created: '2026-11-01T03:39:01Z'
---
client tools/track.sh blocked() waits without end until Private DNS applies; on a run it never applied until the emulator's wifi was toggled (client-host-runelite-fetches hand-off). Make up re-apply the setting (wifi off/on) when the observed DNS state does not change after the setting is written, and fail with the observed state if it still does not apply. No timers. One test per requirement touched.
